---
services: virtual-machines
platforms: python
author: zivraf
---

# Collecting Scheduled Events with Event Hub  

## About this sample
The sample project demonstrates how to monitor upcoming events on multiple Virtual Machines by forwarding them to a single Event Hub.

Scheduled Events is one of the subservices under Azure Metadata Service that surfaces information regarding upcoming events (for example, reboot). Scheduled events give your application sufficient time to perform preventive tasks to minimize the effect of such events. Being part of the Azure Metadata Service, scheduled events are surfaced using a REST Endpoint from within the VM. The information is available via a Non-routable IP so that it is not exposed outside the VM. 

However, there are cases where you wish to have a single endpoint from which you can monitor multiple VMs across one or more Azure regions. This sample, installed in each of your VMs (potentially as VM extension) monitors the Metadata endpoint and forward scheduled events to a central Event Hub.


## Building the sample
1. You will need an Event Hub created before runnign the sample. To do this, refer to the article [Create an Event Hub through Azure Portal](https://docs.microsoft.com/en-us/azure/event-hubs/event-hubs-create).

2. Copy the connection string for your Event Hub and paste it in the configuration file. This is the 'RootManageSharedAccessKey' under Shared Access Policies.

3. At the end of the Event Hub connection string, add ";EntityPath=[your-eventhub-name]", where your-eventhub-name is the name of the event hub that will be handling the events.

4. This sample was tested on PYthon 3.5 


## Running the sample
You can run this sample interactively from your command prompt or shell window.
1. Modify scheduledEventsInteractiveToolConfig.ini with your Event Hub connection string and event hub name.
2. Run the sample from your shell 
    ```
     python3 scheduledEventsInteractiveTool.py
    ```
    
    A successful run will emit some info and debug data (which you can filter out):

   ```
   2017-04-17 18:18:06,632 [DEBUG] Azure Scheduled Events Interactive Tool
   2017-04-17 18:18:06,632 [DEBUG] get_scheduled_events was called
   2017-04-17 18:18:06,639 [INFO] handle_scheduled_events was called with 0
   2017-04-17 18:18:07,816 [DEBUG] send_to_event_hub returned
   ```

   In case a scheduled event is detected, the sample sends a notification to Event Hub and acknoledges the scheduled event.
   ```
   myuser@mysrv:~$ python3 scheduledEventsInteractiveTool.py
   2017-04-17 18:30:35,169 [DEBUG] Azure Scheduled Events Interactive Tool
   2017-04-17 18:30:35,169 [DEBUG] get_scheduled_events was called
   2017-04-17 18:30:35,175 [INFO] handle_scheduled_events was called with 1
   2017-04-17 18:30:35,175 [INFO] EventId: 762D06A2-8289-469B-AB27-4D26C9C745B3 Type: Redeploy Status: Scheduled Resource: _mysrv
   2017-04-17 18:30:35,507 [DEBUG] send_to_event_hub returned
   2017-04-17 18:30:35,507 [INFO] THIS host is scheduled for Redeploy not before Mon,_17_Apr_2017_18:40:06_GMT
   Are you looking to acknowledge the event (y/n)? n

   ```
  You can also acknoledge the event from the sample. In this case, you ask Azure to move faster with the impact. 

3. Check your Event Hub for messages. You can use [Service Bus Explorer](https://github.com/paolosalvatori/ServiceBusExplorer) to check for the messages sent to Event Hub. 

