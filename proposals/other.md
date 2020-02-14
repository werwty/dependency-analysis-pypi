## Other Ideas

### Measuring the security risk of using unencrypted Wifi hotspots.

Eavesdropping and MITM on an open Wifi network are less attractive than they were 10 years ago. Today, the standardized beamforming technique that comes with 802.11ac makes sniffing the traffic between beamforming-enabled devices harder (the sniffer must be placed at the right location). Modern websites and applications also tend to less vulnerable to eavesdropping and MITM because of the adoption of TLS.

However, the traffic of legacy 802.11a/b/g/n clients that don't support beamforming is still easy to catch. Even though most application use TLS, there are some that do not implement TLS correctly. There is also the risk of side channel attacks on DNS traffic and others that can expose the user's privacy.

For the above reason, we may need to reevaluate the security risk of using open Wifi today, and how hard it is to attack open Wifi with today's commodity hardware. We propose a measurement study across NCSU to measure the number of sites still vulnerable to privacy leakage, MITM attacks, and other side channel attacks. 

NCSU currently provides three Wifi hotspots: eduroam (protected by WPA2-Enterprise), ncsu (open), ncsu-guest (open). According to daily experience, lots of students don't use eduroam because it needs to go through an extra enrolling process. If ethical and allowed, we can perform a measurement by launching anonymous traffic sniffing on ncsu and ncsu-guest network. This research have a positive meaning to the campus: it help people understand when shouldn't use unencrypted ncsu/ncsu-guest network.


Open Questions:
- Can this get pass an IRB?
- How can we get enough hardware to eavesdrop across campus? 


### Measurment of Post-Quantum Cryptography Protocol Usage in the Wild

Nowadays new crypto protocols have to claim post quantum security to be taken seriously, but what is the actual adoption of post-quantum secure protocols?
 What is causing the big gap between quantum based crypto protocols and their implementation and usage? 
 
It would be interesting to do a measurement on the current adoption of post-quantum cryptographic protocols, this can be the first in a longitudinal studies so we can observe the adoption of post-quantum protocols.

We can find the crypto libraries that have post-quantum support and then scan github for how common those features are used. 

We'll either find: 1. there is close to zero adoption (most likely) or 2. There is some small adoption. We can reason about and who are the early adopter of post-quantum protocols and reason about the users of such applications/libraries.
If #1 is found, how much of this is because of how the crypto libraries are written? Are these protocols just not ready for mainstream usage? Are they just confusing/hard to use? How are they documented differently from traditional crypto protocols? Is it just a matter of the general public needing more education? Or is the runtime of these significantly worse and therefore not worth the tradeoff?

