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
1. You will need an Event Hub created before runnign the sample. To do this, refer to the article [Create an IoT Hub through Azure Portal](https://azure.microsoft.com/documentation/articles/iot-hub-csharp-csharp-getstarted/#create-an-iot-hub).

2. Copy the connection string for your Event Hub and paste it in the configuration file.

3. This sample was tested on PYthon 3.5 


## Running the sample
You can run this sample interactively from your command prompt or shell window.

You can also schedule this utility to run periodically in the background with your platform's scheduled (e.g. cron) 