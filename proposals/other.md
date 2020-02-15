## Other Ideas

## Measurement of Post-Quantum Cryptography Protocol Usage in the Wild

Nowadays new crypto protocols have to claim post quantum security to be taken seriously, but what is the actual adoption of post-quantum secure protocols?
 What is causing the big gap between quantum based crypto protocols, their implementations and their usage? 
 
It would be interesting to do a measurement on the current adoption of post-quantum cryptographic protocols, this can be the first in a longitudinal studies so we can observe the adoption of post-quantum protocols.

We can find the crypto libraries that have post-quantum support and then scan github for how common those features are used. 

We'll either find: 1. there is close to zero adoption (most likely) or 2. There is some small adoption. 

We can reason about and who are the early adopter of post-quantum protocols and reason about the users of such applications/libraries.
If #1 is found, how much of this is because of how the crypto libraries are written? Are these protocols just not ready for mainstream usage? Are they just confusing/hard to use? How are they documented differently from traditional crypto protocols? Is it just a matter of the general public needing more education? Or is the runtime of these significantly worse and therefore not worth the tradeoff?
