import re
from statistics import mean

data = """
1746428427.5971909: Starting mining process...

1746428427.5994835: Mining process started.

1746428429.8845358: Chain extended: <block.Block object at 0x7f9b30e72680>

1746428430.4626067: Chain extended: <block.Block object at 0x7f9b30e72560>

1746428436.9248846: Chain extended: <block.Block object at 0x7f9b30e725c0>

1746428439.4993536: Chain extended: <block.Block object at 0x7f9b30e72650>

1746428446.8339727: Chain extended: <block.Block object at 0x7f9b30e724d0>

1746428453.2142966: Chain extended: <block.Block object at 0x7f9b30e72d10>

1746428475.074687: Chain extended: <block.Block object at 0x7f9b30e72d70>

1746428476.202789: Chain extended: <block.Block object at 0x7f9b30e72ce0>

1746428496.5850682: Chain extended: <block.Block object at 0x7f9b30e72dd0>

1746428498.5078433: Chain extended: <block.Block object at 0x7f9b30e72d40>

1746428525.4952679: Chain extended: <block.Block object at 0x7f9b30e72e30>

1746428528.7145805: Chain extended: <block.Block object at 0x7f9b30e72da0>

1746428561.840587: Chain extended: <block.Block object at 0x7f9b30e72e90>

1746428586.0436172: Chain extended: <block.Block object at 0x7f9b30e72e60>

1746428599.7944589: Chain extended: <block.Block object at 0x7f9b30e72e00>

1746428653.6107593: Chain extended: <block.Block object at 0x7f9b30e72f20>

1746428671.8415055: Chain extended: <block.Block object at 0x7f9b30e72f50>

1746428674.9763165: Chain extended: <block.Block object at 0x7f9b30e72ef0>

1746428704.653119: Chain extended: <block.Block object at 0x7f9b30e72f80>

1746428737.888213: Chain extended: <block.Block object at 0x7f9b30e72fe0>

1746428813.5468988: Chain extended: <block.Block object at 0x7f9b30e72ec0>

1746428902.5351691: Chain extended: <block.Block object at 0x7f9b30e73040>

1746428905.0166268: Chain extended: <block.Block object at 0x7f9b30e73070>

1746428906.0872726: Chain extended: <block.Block object at 0x7f9b30e73010>

1746428912.7200038: Chain extended: <block.Block object at 0x7f9b30e730d0>

1746428934.8296006: Chain extended: <block.Block object at 0x7f9b30e730a0>

1746428944.403355: Chain extended: <block.Block object at 0x7f9b30e72fb0>

1746429046.7507865: Chain extended: <block.Block object at 0x7f9b30e73100>

1746429086.978793: Chain extended: <block.Block object at 0x7f9b30e73190>

1746429154.868424: Chain extended: <block.Block object at 0x7f9b30e731c0>

1746429167.0843358: Chain extended: <block.Block object at 0x7f9b30e73130>

1746429379.728222: Chain extended: <block.Block object at 0x7f9b30e73220>

1746429418.5869045: Chain extended: <block.Block object at 0x7f9b30e731f0>

1746429420.6341577: Chain extended: <block.Block object at 0x7f9b30e73160>

1746429433.124508: Chain extended: <block.Block object at 0x7f9b30e732b0>

1746429449.5088308: Chain extended: <block.Block object at 0x7f9b30e732e0>

1746429461.3388095: Chain extended: <block.Block object at 0x7f9b30e73280>

1746429473.2230515: Chain extended: <block.Block object at 0x7f9b30e73310>

1746429482.3577273: Chain extended: <block.Block object at 0x7f9b30e73250>

1746429538.5554771: Chain extended: <block.Block object at 0x7f9b30e73340>

1746429538.9112048: Chain extended: <block.Block object at 0x7f9b30e733a0>

1746429620.6599593: Chain extended: <block.Block object at 0x7f9b30e73400>

1746429695.273976: Chain extended: <block.Block object at 0x7f9b30e73370>

1746429809.774062: Chain extended: <block.Block object at 0x7f9b30e733d0>

1746429811.8224168: Chain extended: <block.Block object at 0x7f9b30e73430>

1746429817.5762718: Chain extended: <block.Block object at 0x7f9b30e73460>

1746429871.7843535: Chain extended: <block.Block object at 0x7f9b30e734c0>

1746429872.4908009: Chain extended: <block.Block object at 0x7f9b30e734f0>

1746429887.883714: Chain extended: <block.Block object at 0x7f9b30e73490>

1746429893.531277: Chain extended: <block.Block object at 0x7f9b30e73520>

1746429918.341168: Chain extended: <block.Block object at 0x7f9b30e73550>

1746429970.670206: Chain extended: <block.Block object at 0x7f9b30e735b0>

1746429975.9485056: Chain extended: <block.Block object at 0x7f9b30e735e0>

1746429979.0713787: Chain extended: <block.Block object at 0x7f9b30e73640>

1746430024.2371476: Chain extended: <block.Block object at 0x7f9b30e73670>

1746430115.4331858: Chain extended: <block.Block object at 0x7f9b30e73610>

1746430140.2240858: Chain extended: <block.Block object at 0x7f9b30e736d0>

1746430227.4925556: Chain extended: <block.Block object at 0x7f9b30e736a0>

1746430351.3205674: Chain extended: <block.Block object at 0x7f9b30e73580>

1746430396.9515254: Chain extended: <block.Block object at 0x7f9b30e73760>

1746430397.197375: Chain extended: <block.Block object at 0x7f9b30e73700>

1746430397.4102192: Chain extended: <block.Block object at 0x7f9b30e73790>

1746430434.9978704: Chain extended: <block.Block object at 0x7f9b30e737f0>

1746430437.2739475: Chain extended: <block.Block object at 0x7f9b30e73820>

1746430451.9105718: Chain extended: <block.Block object at 0x7f9b30e73850>

1746430486.6157794: Chain extended: <block.Block object at 0x7f9b30e73730>

1746430497.1220658: Chain extended: <block.Block object at 0x7f9b30e73880>

1746430502.1178694: Chain extended: <block.Block object at 0x7f9b30e738e0>

1746430559.4997487: Chain extended: <block.Block object at 0x7f9b30e737c0>

1746430606.865957: Chain extended: <block.Block object at 0x7f9b30e73940>

1746430632.1659553: Chain extended: <block.Block object at 0x7f9b30e73910>

1746430638.270858: Chain extended: <block.Block object at 0x7f9b30e738b0>

1746430649.572307: Chain extended: <block.Block object at 0x7f9b30e739d0>

1746430684.2467535: Chain extended: <block.Block object at 0x7f9b30e73970>

1746430695.0901926: Chain extended: <block.Block object at 0x7f9b30e73a30>

1746430703.8545058: Chain extended: <block.Block object at 0x7f9b30e739a0>

1746430779.3659205: Chain extended: <block.Block object at 0x7f9b30e73a00>

1746430840.6026802: Chain extended: <block.Block object at 0x7f9b30e73ac0>

1746430918.2220833: Chain extended: <block.Block object at 0x7f9b30e73a60>

1746430963.5107572: Chain extended: <block.Block object at 0x7f9b30e73a90>

1746430968.7004871: Chain extended: <block.Block object at 0x7f9b30e73b50>

1746430970.2837772: Chain extended: <block.Block object at 0x7f9b30e73af0>

1746430977.82854: Chain extended: <block.Block object at 0x7f9b30e73b80>

1746431059.1331823: Chain extended: <block.Block object at 0x7f9b30e73bb0>

1746431066.743901: Chain extended: <block.Block object at 0x7f9b30e73c10>

1746431416.7931495: Chain extended: <block.Block object at 0x7f9b30e73be0>

1746431491.4330468: Chain extended: <block.Block object at 0x7f9b30e73b20>

1746431495.4707854: Chain extended: <block.Block object at 0x7f9b30e73c70>

1746431501.3874307: Chain extended: <block.Block object at 0x7f9b30e73ca0>

1746431512.7804823: Chain extended: <block.Block object at 0x7f9b30e73d00>

1746431517.982652: Chain extended: <block.Block object at 0x7f9b30e73cd0>

1746431535.6600213: Chain extended: <block.Block object at 0x7f9b30e73d30>

1746431548.7442985: Chain extended: <block.Block object at 0x7f9b30e73d90>

1746431552.5723271: Chain extended: <block.Block object at 0x7f9b30e73c40>

1746431556.5672534: Chain extended: <block.Block object at 0x7f9b30e73df0>

1746431564.5772161: Chain extended: <block.Block object at 0x7f9b30e73d60>

1746431573.3298223: Chain extended: <block.Block object at 0x7f9b30e73dc0>

1746431610.260474: Chain extended: <block.Block object at 0x7f9b30e73e50>

1746431680.2602074: Chain extended: <block.Block object at 0x7f9b30e73eb0>

1746432004.7657545: Chain extended: <block.Block object at 0x7f9b30e73e20>

1746432037.4719136: Chain extended: <block.Block object at 0x7f9b30e73f10>

1746432085.5822177: Chain extended: <block.Block object at 0x7f9b30e73fd0>

1746432232.822334: Chain extended: <block.Block object at 0x7f9b30e73fa0>

1746432278.6438143: Chain extended: <block.Block object at 0x7f9b30e73ee0>

1746432287.1611888: Chain extended: <block.Block object at 0x7f9b30c000d0>

1746432297.8675623: Chain extended: <block.Block object at 0x7f9b30c00100>

1746432307.1681511: Chain extended: <block.Block object at 0x7f9b30c00130>

1746432312.7040808: Chain extended: <block.Block object at 0x7f9b30c00160>

1746432332.7396939: Chain extended: <block.Block object at 0x7f9b30c00190>

1746432350.3148959: Chain extended: <block.Block object at 0x7f9b30c001c0>

1746432404.9805431: Chain extended: <block.Block object at 0x7f9b30c001f0>

1746432430.5587265: Chain extended: <block.Block object at 0x7f9b30c00220>

1746432450.4660842: Chain extended: <block.Block object at 0x7f9b30c00250>

1746432457.9503832: Chain extended: <block.Block object at 0x7f9b30c00280>

1746432536.4191773: Chain extended: <block.Block object at 0x7f9b30c002b0>

1746432635.3853457: Chain extended: <block.Block object at 0x7f9b30c002e0>

1746432667.7576845: Chain extended: <block.Block object at 0x7f9b30c00310>

1746432677.0932534: Chain extended: <block.Block object at 0x7f9b30c00340>

1746432745.259562: Chain extended: <block.Block object at 0x7f9b30c00370>

1746432757.2373104: Chain extended: <block.Block object at 0x7f9b30c003a0>

1746432770.0755832: Chain extended: <block.Block object at 0x7f9b30c003d0>

1746432786.8235335: Chain extended: <block.Block object at 0x7f9b30c00400>

1746432799.3313305: Chain extended: <block.Block object at 0x7f9b30c00430>

1746432821.2857556: Chain extended: <block.Block object at 0x7f9b30c00460>

1746432829.0699136: Chain extended: <block.Block object at 0x7f9b30c00490>

1746432836.4197345: Chain extended: <block.Block object at 0x7f9b30c004c0>

1746432845.1652713: Chain extended: <block.Block object at 0x7f9b30c004f0>

1746432857.2617083: Chain extended: <block.Block object at 0x7f9b30c00520>

1746432877.9162393: Chain extended: <block.Block object at 0x7f9b30c00550>

1746432997.1193604: Chain extended: <block.Block object at 0x7f9b30c00580>

1746433228.9579737: Chain extended: <block.Block object at 0x7f9b30c005b0>

1746433234.7065003: Chain extended: <block.Block object at 0x7f9b30c005e0>

1746433270.7870786: Chain extended: <block.Block object at 0x7f9b30c00610>

1746433352.171463: Chain extended: <block.Block object at 0x7f9b30c00640>

1746433415.7180014: Chain extended: <block.Block object at 0x7f9b30c00670>

1746433435.9496622: Chain extended: <block.Block object at 0x7f9b30c006a0>

1746433439.024109: Chain extended: <block.Block object at 0x7f9b30c006d0>

1746433448.1504712: Chain extended: <block.Block object at 0x7f9b30c00700>

1746433789.1250606: Chain extended: <block.Block object at 0x7f9b30c00730>

1746433792.4556289: Chain extended: <block.Block object at 0x7f9b30c00760>

1746433807.4682102: Chain extended: <block.Block object at 0x7f9b30c00790>

1746433822.5895085: Chain extended: <block.Block object at 0x7f9b30c007c0>

1746433825.8239124: Chain extended: <block.Block object at 0x7f9b30c007f0>

1746433833.496283: Chain extended: <block.Block object at 0x7f9b30c00820>

1746433835.4624093: Chain extended: <block.Block object at 0x7f9b30c00850>

1746433854.879334: Chain extended: <block.Block object at 0x7f9b30c00880>

1746433862.0709808: Chain extended: <block.Block object at 0x7f9b30c008b0>

1746433866.1339598: Chain extended: <block.Block object at 0x7f9b30c008e0>

1746433882.676751: Chain extended: <block.Block object at 0x7f9b30c00910>

1746433934.2754214: Chain extended: <block.Block object at 0x7f9b30c00940>

1746433940.8690197: Chain extended: <block.Block object at 0x7f9b30c00970>
"""

# printing some stats about times between the timestamps
# Extract timestamps from the data
timestamps = [float(match.group(1)) for match in re.finditer(r"(\d+\.\d+):", data)]

# Calculate time differences
time_differences = [timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps))]

# Print statistics
print(f"Total events: {len(timestamps)}")
print(f"Average time between events: {mean(time_differences):.2f} seconds")
print(f"Minimum time between events: {min(time_differences):.2f} seconds")
print(f"Maximum time between events: {max(time_differences):.2f} seconds")
import matplotlib.pyplot as plt

# Plot the time differences
plt.figure(figsize=(10, 6))
plt.plot(time_differences, marker='o', linestyle='-', color='b')
plt.title("Time Differences Between Events")
plt.xlabel("Event Index")
plt.ylabel("Time Difference (seconds)")
plt.grid(True)
plt.show()