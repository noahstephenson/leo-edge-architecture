# Hand calculation for product size

A smaller product saves delivery time when transmitting the removed bytes would take longer than the processing time still exposed to the user. With sizes in bytes and rate in bits per second:

`exposed processing time < 8 × (raw bytes − product bytes) / link rate`.

Processing can begin after collection, before a terminal contact starts. The time left at contact is `max(0, processing time − lead time)`, where lead time is the interval available for processing before contact.

For a one billion byte raw scene, an assumed 300 million byte compressed scene, and a 5 megabit per second link, the transfer saving is `8 × 700,000,000 / 5,000,000 = 1,120 seconds`. If processing takes 20 seconds and begins at contact, the simple net timing advantage is 1,100 seconds. At 50 megabits per second the transfer saving is 112 seconds and the net is 92 seconds.

The calculation checks units and gives a first estimate. It leaves out collection waits, missed contacts, transfers across later contacts, and terminal derivation. Compression may also change image quality. The [contact model](MODEL_REFERENCE.md) adds those timing effects; the [current evidence](../results/current/parametric.csv) records selected parameter cases.
