"""Bounded paired sensitivities and exact filters for reported claims."""
from collections import defaultdict
import csv
import hashlib
import json
import random
from itertools import combinations
from statistics import mean
from e11_mission_thread_success import (
    ARCHITECTURE_FACTORIES, CONDITIONS, MISSION_THREADS, TERMINAL_CLASSES,
    PROCESSING_TIME_S, evaluate_single_request,
)
from leo_edge.stats import paired_bootstrap_diff_ci, wilson_ci


def select(rows, filters):
    return [r for r in rows if all(str(r[k]) == str(v) for k, v in filters.items())]


def additional_evidence(output, single, hours, trials, seed, access, context, write_csv, write_json):
    nominal = CONDITIONS['NOMINAL']
    degraded = CONDITIONS['COMBINED_DEGRADED']
    cases = [dict(case='baseline', condition=nominal)]
    for key in ('tasking_delay_s', 'interference_derate', 'contact_denial_frac'):
        cases.append(dict(case=key, condition={**nominal, key: degraded[key]}))
    for factor in (0.5, 2.0):
        cases.append(dict(case=f'rate_{factor:g}x', condition=nominal, rate_factor=factor))
        cases.append(dict(case=f'processing_{factor:g}x', condition=nominal, processing_factor=factor))
    cases.extend([dict(case='sampling_5s', condition=nominal, step=5),
                  dict(case='next_day', condition=nominal, offset=86400),
                  dict(case='aoi_shift_1deg', condition=nominal, shift=1)])
    cache, rows = {}, []
    thread = MISSION_THREADS['MT2_ROUTE_RECON_FIRST']
    for case in cases:
        geometry = (case.get('step', 30), case.get('offset', 0), case.get('shift', 0))
        if geometry not in cache:
            aoi, links = access((24, 8, 1), hours, *geometry, single_site_only=True)
            cache[geometry] = aoi, links[1]
        aoi, downlink = cache[geometry]
        # A dedicated seed gives the same request/prior draw in every case.
        # Denial uniforms use a separate stream so different contact counts
        # never change later request draws. Draws align by contact ordinal,
        # not physical contact identity when geometry changes.
        requests = random.Random(f'{seed}:sensitivity:requests')
        terminal = {**TERMINAL_CLASSES['DISMOUNTED_MANPACK']}
        terminal['rate_bps'] *= case.get('rate_factor', 1)
        processing = PROCESSING_TIME_S * case.get('processing_factor', 1)
        for trial in range(trials):
            request = requests.uniform(0, max(0, hours * 3600 - 3600))
            prior = requests.random()
            ctx = context(random.Random(f'{seed}:context:{trial}'), case['condition'], aoi, downlink, hours * 3600)
            from e11_mission_thread_success import next_collection_event
            collection = next_collection_event(request + case['condition']['tasking_delay_s'], aoi)
            windows = downlink[collection[1]] if collection else []
            denials = random.Random(f'{seed}:sensitivity:denials:{trial}')
            ctx.update(request_time_s=request, prior_reference_roll=prior, collection=collection,
                       downlink_windows=windows, denial_rolls=[denials.random() for _ in windows])
            digest = hashlib.sha256(json.dumps(ctx, sort_keys=True).encode()).hexdigest()
            for arch, factory in ARCHITECTURE_FACTORIES.items():
                result = evaluate_single_request(factory, 'MT2_ROUTE_RECON_FIRST', thread,
                    'DISMOUNTED_MANPACK', terminal, case['case'], case['condition'], ctx, trial,
                    processing_time_s=processing)
                rows.append(dict(case=case['case'], architecture_id=arch, trial=trial,
                    paired_context_sha256=digest, request_time_s=request,
                    sampling_step_s=geometry[0], propagation_offset_s=geometry[1], aoi_shift_deg=geometry[2],
                    rate_bps=terminal['rate_bps'] * case['condition']['interference_derate'],
                    processing_time_s=processing, tasking_delay_s=case['condition']['tasking_delay_s'],
                    denial_fraction=case['condition']['contact_denial_frac'],
                    success=result['success'], latency_s=result['latency_s'], outcome=result['outcome'],
                    collection_delay_s=result['collection_delay_s'],
                    full_scene_latency_s=result['full_scene_latency_s']))
    write_csv(output / 'sensitivity_trials.csv', rows)
    groups = defaultdict(list)
    for row in rows:
        groups[(row['case'], row['architecture_id'])].append(row)
    summary = []
    for (case, arch), group in groups.items():
        successes = sum(r['success'] for r in group)
        lo, hi = wilson_ci(successes, len(group))
        base = groups[('baseline', arch)]
        summary.append(dict(case=case, architecture_id=arch, n_trials=len(group), successes=successes,
            success_rate=successes / len(group), ci95_lower=lo, ci95_upper=hi,
            classification_changes_from_baseline=sum(a['success'] != b['success'] for a, b in zip(group, base))))
    write_csv(output / 'sensitivity_summary.csv', summary)
    paired = []
    for case in [c['case'] for c in cases]:
        for arch in ARCHITECTURE_FACTORIES:
            group, reference = groups[(case, arch)], groups[(case, 'A0_GROUND_ONLY')]
            diff, lo, hi, _ = paired_bootstrap_diff_ci([r['success'] for r in group], [r['success'] for r in reference], seed=seed)
            paired.append(dict(case=case, architecture_id=arch, reference='A0_GROUND_ONLY',
                               paired_difference=diff, ci95_lower=lo, ci95_upper=hi))
    write_csv(output / 'paired_differences.csv', paired)
    principal = dict(walker='24/8/1', terminal_sites=1, terminal_class='DISMOUNTED_MANPACK',
                     condition='NOMINAL', thread='MT2_ROUTE_RECON_FIRST')
    counter = dict(walker='1/1/0', terminal_sites=4, terminal_class='VEHICLE_MOUNTED',
                   condition='NOMINAL', thread='MT2_ROUTE_RECON_FIRST')
    claims = []
    for label, filters in [('principal', principal), ('counterexample', counter)]:
        for arch in ARCHITECTURE_FACTORIES:
            filt = {**filters, 'architecture_id': arch}
            group = select(single, filt)
            for column in ('success', 'full_scene_deadline_met', 'produced'):
                claims.append(dict(claim=f'{label}_{arch}_{column}', source='single_request_trials.csv',
                    filters=filt, aggregation='count_true', column=column,
                    numerator=sum(r[column] for r in group), denominator=len(group)))
    main_pairs = []
    for left, right in combinations(ARCHITECTURE_FACTORIES, 2):
        a = sorted(select(single, {**principal, 'architecture_id': left}), key=lambda r: r['trial'])
        b = sorted(select(single, {**principal, 'architecture_id': right}), key=lambda r: r['trial'])
        assert [r['paired_context_sha256'] for r in a] == [r['paired_context_sha256'] for r in b]
        difference, lo, hi, _ = paired_bootstrap_diff_ci([r['success'] for r in a], [r['success'] for r in b], seed=seed)
        shared = [x['latency_s'] - y['latency_s'] for x, y in zip(a, b) if x['success'] and y['success']]
        main_pairs.append(dict(candidate_a=left, candidate_b=right, n_pairs=len(a),
            difference_a_minus_b=difference, ci95_lower=lo, ci95_upper=hi,
            both_timely_pairs=len(shared), mean_latency_difference_s=mean(shared) if shared else None,
            interpretation='success-rate difference; latency conditional on both candidates being timely'))
    write_csv(output / 'principal_paired_differences.csv', main_pairs)
    latency = next(r for r in main_pairs if r['candidate_a'] == 'A3_ROI_FIRST' and r['candidate_b'] == 'A6_THREAD_AWARE_PRIORITY')
    claims.append(dict(claim='principal_A3_minus_A6_jointly_timely_latency',
        source='principal_paired_differences.csv', filters=dict(candidate_a='A3_ROI_FIRST', candidate_b='A6_THREAD_AWARE_PRIORITY'),
        aggregation='first_numeric', column='mean_latency_difference_s',
        numerator=latency['mean_latency_difference_s'], denominator=1))
    for row in summary:
        for column in ('successes', 'classification_changes_from_baseline'):
            claims.append(dict(claim=f"sensitivity_{row['case']}_{row['architecture_id']}_{column}",
                source='sensitivity_summary.csv', filters=dict(case=row['case'], architecture_id=row['architecture_id']),
                aggregation='first_numeric', column=column, numerator=row[column], denominator=1))
    # Locate the immutable baseline relative to this module, not output location.
    from pathlib import Path
    old_path = Path(__file__).resolve().parents[1] / 'results/history/pre-completion-2026-09-30/single_request_trials.csv'
    if old_path.exists():
        with old_path.open(newline='') as stream:
            old = list(csv.DictReader(stream))
        key = lambda r: tuple(str(r[k]) for k in ('walker','terminal_sites','terminal_class','condition','thread','trial','architecture_id'))
        lookup = {key(r): r for r in old}
        changes = []
        for row in single:
            previous = lookup[key(row)]
            changes.append(dict(zip(('walker','terminal_sites','terminal_class','condition','thread','trial','architecture_id'), key(row)),
                old_success=previous['success'], new_success=row['success'],
                outcome_changed=(previous['success'] == 'True') != row['success'],
                old_latency_s=previous['latency_s'], new_latency_s=row['latency_s']))
        write_csv(output / 'baseline_comparison.csv', changes)
        claims.append(dict(claim='baseline_changed_deadline_classifications', source='baseline_comparison.csv',
            filters={}, aggregation='count_true', column='outcome_changed',
            numerator=sum(r['outcome_changed'] for r in changes), denominator=len(changes)))
    write_json(output / 'claims.json', claims)
    for claim in claims:
        if claim['source'] == 'single_request_trials.csv':
            assert claim['denominator'] == trials
    for group in groups.values():
        assert len(group) == trials
