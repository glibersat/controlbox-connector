# Controlbox AsyncIO communcation library

## Scope

The goal is to Provide an asynchronous library for controlbox
developers so they just have to write 3rd-party codecs that implement their
domain specific objects to use their protocol.

For example, for a Meteoroly oriented controlbox controller, this means
providing codecs for objects such as "Temperature Sensor" or "Humidity Sensor".

This library handles low-level controlbox standard messages (such as CRUD
messages). It also provides typical transports such as serial line communication
or tcp/ip socket.

The final interface are higher-level objects that looks as pythonic as possible
and provides enough abstraction such as it is easy enough to write a library for
end-users without the need of a deep understanding of the controlbox protocol.

This is not meant to be used directly by protocol integrators: you should
provide your own library/module based on this one.

## Sample usage

### Providing codecs

This part should be written in your protocol library/module.

```python
import controlbox
from controlbox.commands import Enum

MeteorologyObjectTypeEnum = Enum(Byte,
                                 TEMPERATURE_SENSOR = 6,
                                 SETPOINT_SIMPLE = 7
                              
controlbox.register_object_types(MeteorologyObjectTypeEnum)
```


### Communicating with a controller

Connecting to a controller:

```python
from controlbox.controller import Controller
from controlbox.conduit import SerialConduit

# Make a conduit
conduit = SerialConduit("/dev/ttyACM0")
controller = Controller(conduit=conduit)

# Now, connect!
controller.connect()
```

Send commands:

```python
from controlbox.commands import ListObjectsCommandRequest

list_objects_command = ListObjectsCommandRequest.build({"profile_id": 0})
future_answer = controller.send(list_objects_command)
```

Let messages be processed:

```python
loop.create_task(controller.process_messages())
```

### Integrating into a end-user software

For example, you'll want to integrate Controlbox commands into a REST paradigm.

For that, make your controller accessible somewhere (let's suppose here it is
globally available) and do it like this:

```python
async def list_objects(request):
  list_objects_command = ListObjectsCommandRequest.build({"profile_id": 0})
  try:
    future = controller.send(list_objects_command)
    response = await future.result()
  except asyncio.TimeoutError:
    raise "504 Gateway Timeout"

  return Response(status=200, body=self.resource.encode(response.encode_to_json()), 
                                                        content_type='application/json')
```
