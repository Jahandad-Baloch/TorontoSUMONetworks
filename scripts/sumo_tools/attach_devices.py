# path: scripts/sumo_tools/attach_devices.py
# Description: This script is used to attach SUMO devices to the vehicles and/or other components in the network.

""" 

Devices
Vehicle devices are used to model and configure different aspects such as output (device.fcd) or behavior (device.rerouting).

The following device names are supported and can be used for the placeholder <DEVICENAME> below

emission
battery
stationfinder
elechybrid
btreiver
btsender
bluelight
rerouting
ssm
toc
driverstate
fcd
tripinfo
vehroute
taxi
glosa
example


Automatic assignment
Some devices are assigned automatically. Every <trip> that is loaded into the simulation is automatically equipped with a rerouting device to perform the initial route computation.

Other devices such as fcd are assigned automatically when the option --fcd-output is set.

Assignment by global options
Devices can be configured globally for all vehicles in the simulation by setting the option --device.<DEVICENAME>.probability (e.g. --device.fcd.probability 0.25. This will equip about a quarter of the vehicles with an fcd device (each vehicle determines this randomly with 25% probability).) To make the assignment exact the additional option --device.<DEVICENAME>.deterministic can be set. Another option is to pass the list of vehicle ids that shall be equipped using the option --device.<DEVICENAME>.explicit <ID1,ID2,...IDk>.

!!! note These options take precedence over automatic assignment by output-option.

Assignment by generic parameters
Another option for assigning devices for vehicle types or individual vehicles is by using generic parameters. This is done by defining them for the vehicle or the vehicle type in the following way:

<routes>
    <vehicle id="v0" route="route0" depart="0">
        <param key="has.<DEVICENAME>.device" value="true"/>
    </vehicle>

    <vType id="t1">
        <param key="has.<DEVICENAME>.device" value="true"/>
    </vType>

    <vehicle id="v1" route="route0" depart="0" type="t1"/>

    <vType id="t2">
        <param key="device.<DEVICENAME>.probability" value="0.5"/>
    </vType>

    <vehicle id="v2" route="route0" depart="0" type="t2"/>
</routes>
!!! note The <param> of a vehicle has precedence over the <param> of the vehicle's type. Both have precedence over the assignment by options.


how to implement a new device.

What is a device good for?
A device is a container for data and functionality which resides in individual vehicles. Devices are notified about all vehicle movements and may interact with the vehicle or with other devices. An important aspect of devices is, that it is possible to equip only a fraction of the simulated vehicles. Usually devices support some kind of output. The following is a list of available devices and their functionality

MSDevice_Tripinfo
Records start and arrival of a vehicle as well as aggregate measures about a completed trip such as average speed and waiting time. This device is also used for expressing aggregate results from other devices such as emissions (MSDevice_HBEFA). This devices is activated using the option --tripinfo-output {{DT_FILE}} and is then active for all vehicles.

MSDevice_Vehroutes
Records the edges traveled by a vehicle and optionally the times at which each edge was left. It can also record dynamic route changes. This device is also used for expressing aggregate results from other devices such as emissions (MSDevice_HBEFA). This devices is activated using the option --vehroute-output {{DT_FILE}} and is then active for all vehicles.

MSDevice_Routing
Triggers periodic rerouting of equipped vehicles. This devices is activated using the options --vehroute-output.* and is then active for selected vehicles. It is possible to equip specific vehicles or a fraction of the vehicle fleet.

MSDevice_Person
This device is automatically created if a person rides in a vehicle. It is used when managing boarding and alighting

MSDevice_HBEFA
Computes emissions of a vehicle as described in Definition_of_Vehicles,_Vehicle_Types,_and_Routes#Vehicle_Emission_Classes. This devices is activated using the options --device.hbefa.* and is then active for selected vehicles. It is possible to equip specific vehicles or a fraction of the vehicle fleet.

MSDevice_Battery
This device is used for modelling energy use and battery capacity of electric vehicles.

MSDevice_SSM
This device logs surrogate safety measures for equipped vehicles, see Simulation/Output/SSM_Device.

MSDevice_Example
This device serves as an implementation example for custom devices.

Steps for implementing a new device
Copy Example Device
The suggested way for creating a new device is to create a new class by copying the files src/microsim/devices/MSDevice_Example.{h,cpp}.

In order to compile the new class it must be added to src/microsim/devices/Makefile.am (on Linux) or added to project z_libmicrosim_devices (on Windows).

In order to be available for use, the device must also be added in src/microsim/devices/MSDevice.cpp to the functions insertOptions and buildVehicleDevices.

Assign Device to Vehicles
Devices are assigned by global options for equipping all or a fraction of the vehicle fleet. Alternatively, they can be defined by setting <vehicle> or <vType>-generic parameters. The new assignment options are generated automatically by calling the function MSDevice::insertDefaultAssignmentsOptions. The test whether a specific vehicle should be equipped with the device is done by calling MSDevice::equippedByDefaultAssignmentOptions. The usage of these methods is demonstrated in MSDevice_Example.

Adding your own functionality
Devices work by updating their state periodically (i.e. MSDevice_Routing) or every time the vehicle moves (i.e. MSDevice_Battery). Many devices perform some kind of output either periodically (MSDevice_Routing) in response to computed events (MSDevice_BTreceiver) or at the time the vehicle leaves the simulation (MSDevice_Vehroutes). Before the vehicle is removed the method generateOutput is called for each device.
"""


""" 
Idea:
1. Device selection and proposed implementation
2. Device assignment and configuration
3. Device output and visualization
4. Device interaction and data exchange
5. Device testing and validation
6. Device documentation and examples
7. Device integration and deployment
8. Device performance and optimization
9. Device maintenance and updates
10. Device support and troubleshooting


"""