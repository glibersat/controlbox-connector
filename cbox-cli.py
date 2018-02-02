#!/usr/bin/env python3
import logging
import time

import coloredlogs
import yaml

from prompt_toolkit import prompt
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token

from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import HSplit, Container
from prompt_toolkit.layout.margins import PromptMargin


from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.shortcuts import create_eventloop

from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FillControl, UIControl, TokenListControl
from prompt_toolkit.layout.controls import UIContent
from prompt_toolkit.layout.dimension import LayoutDimension as D
from prompt_toolkit.layout.margins import NumberredMargin, ScrollbarMargin

from pygments.token import Token

from prompt_toolkit.contrib.completers import WordCompleter

import argparse
from argparse import ArgumentParser
from prompt_toolkit.buffer import AcceptAction
from prompt_toolkit.layout.lexers import PygmentsLexer
from prompt_toolkit.styles.from_pygments import style_from_pygments
from pygments.styles import get_style_by_name

# TEMP
import serial
from protocol import (
    ActivateProfileCommandRequest,
    ReadValueCommandRequest,
    ListObjectsCommandRequest,
    ResetCommandRequest,
    CreateObjectCommandRequest,
    ListProfilesCommandRequest
)


command_completer = WordCompleter([
    'profile',
    'object',
    'eeprom',
    'read',
    'activate',
    'list'
], ignore_case=True)





from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.keys import Keys


from logging import Handler

class ConsoleHandler(Handler):
    def __init__(self, buffer, cli):
        super().__init__(level=logging.DEBUG)
        self.buffer = buffer
        self.cli = cli

    def emit(self, record):
        log_entry = self.format(record)
        self.buffer.insert_text(log_entry)
        self.buffer.newline()
        self.cli.request_redraw()


class StatusBarArgumentParser(ArgumentParser):
    def __init__(self, prog, app):
        self.app = app
        super().__init__(prog=prog, add_help=False)

    def error(self, message):
        raise Exception(message)


class BrewPiCommandParser:
    def __init__(self, app):
        self.app = app

        self.parser = StatusBarArgumentParser(prog="cbox", app=app)
        subparsers = self.parser.add_subparsers(dest="cmd")

        # Mode
        # parser_profile = subparsers.add_parser(name='profile', app=app, help="switch control mode")
        # parser_profile.add_argument('action', help="manage profiles", choices=['create', 'list', 'activate', 'delete'])

        # Profiles
        parser_profile = subparsers.add_parser(name='profile', app=app, help="manage profiles")
        parser_profile_subparsers = parser_profile.add_subparsers(dest='profile_cmd')
        # parser_profile_list = parser_device_subparsers.add_parser(name='list', app=app, help="List devices")
        # parser_device_list.add_argument('which', choices=['available', 'installed'])

        parser_profile_activate = parser_profile_subparsers.add_parser(name='activate', app=app, help="Activate a profile")
        parser_profile_activate.add_argument('profile_id', help="Profile ID")

        parser_profile_list = parser_profile_subparsers.add_parser(name='list', app=app, help="List profiles")

        # Objects
        parser_object = subparsers.add_parser(name='object', app=app, help="manage objects")
        parser_object_subparsers = parser_object.add_subparsers(dest='object_cmd')

        parser_object_read = parser_object_subparsers.add_parser(name='read', app=app, help="Read an object")
        parser_object_read.add_argument('object_id', help="Object ID")

        parser_object_list = parser_object_subparsers.add_parser(name='list', app=app, help="List objects of profile")
        parser_object_list.add_argument('profile_id', help="Profile ID")

        parser_object_create = parser_object_subparsers.add_parser(name='create', app=app, help="Create objects in profile")


        parser_eeprom = subparsers.add_parser(name='eeprom', app=app, help="Eeprom management")
        parser_eeprom.add_argument('eeprom_cmd', help="manage eeprom", choices=['erase'])


        # parser_device_install_subparsers = parser_device_install.add_subparsers(dest='install_hwtype')

        # Temperature sensor
        # parser_device_install_temp_sensor = parser_device_install_subparsers.add_parser(name='temperature_sensor', app=app, help="Hardware Type")
        # parser_device_install_temp_sensor.add_argument('address', help="1-wire address")
        # parser_device_install_temp_sensor.add_argument('function', choices=['beer', 'chamber', 'room'], help="Which function to assign to.")

        # Heater/Cooler
        # parser_device_install_heater = parser_device_install_subparsers.add_parser(name='heater', app=app, help="Install Heater")
        # parser_device_install_heater.add_argument('pin', help="pin where to install")

        # Heater/Cooler
        # parser_device_install_cooler = parser_device_install_subparsers.add_parser(name='cooler', app=app, help="Install Cooler")
        # parser_device_install_cooler.add_argument('pin', help="pin where to install")


        # Macro
        parser_mode = subparsers.add_parser(name='macro', app=app, help="run a macro")
        parser_mode.add_argument('file', help="Name of macro file")
        parser_mode.add_argument('name', help="Name of the macro")


    def parse(self, cli, buffer):
        curr_line = buffer.document.current_line
        self.parse_line(cli, curr_line, buffer)

    def parse_line(self, cli, line, buffer):
        args = None
        line = line.split()
        try:
            args, leftovers = self.parser.parse_known_args(args=line)
        except argparse.ArgumentError as e:
            cli.logger.error(e)
        except Exception as e:
            cli.logger.error(e)

        cmd_to_send = None
        if args is not None:
            if args.cmd == 'profile':
                if args.profile_cmd == "list":
                    cmd_to_send = ListProfilesCommandRequest.build({})
                elif args.profile_cmd == "activate":
                    cmd_to_send = ActivateProfileCommandRequest.build({"profile_id": int(args.profile_id)})

            elif args.cmd == 'object':
                if args.object_cmd == "read":
                    cmd_to_send = ReadValueCommandRequest.build({"id": [int(args.object_id)], 'type':"TEMPERATURE_SENSOR"})
                if args.object_cmd == "list":
                    cmd_to_send = ListObjectsCommandRequest.build({"profile_id": int(args.profile_id)})
                if args.object_cmd == "create":
                    from OneWireTempSensor_pb2 import OneWireTempSensor
                    temp_sensor = OneWireTempSensor()
                    temp_sensor.settings.address=0x289E6CFF08000042
                    cmd_to_send = CreateObjectCommandRequest.build(dict(id=[0], type="TEMPERATURE_SENSOR", data=temp_sensor.SerializeToString()))


            elif args.cmd == 'eeprom':
                if args.eeprom_cmd == "erase":
                    cmd_to_send = ResetCommandRequest.build(dict(flags=dict(erase_eeprom=True, hard_reset=True)))


            elif args.cmd == 'macro':
                try:
                    with open("{0}.bpm".format(args.file), 'r') as stream:
                        try:
                            data = yaml.load(stream)
                        except yaml.YAMLError as exc:
                            cli.logger.info(exc)

                        # now run macro
                        try:
                            cmds = data[args.name]

                            for cmd in cmds:
                                self.parse_line(cli, cmd, buffer)
                                cli.logger.info("[{0}] -> {1}".format(args.file, cmd))
                                time.sleep(0.1)
                        except KeyError:
                            cli.logger.warn("No macro named <{0}> in file <{1}.bpm>".format(args.name,
                                                                                            args.file))
                except FileNotFoundError as e:
                    cli.logger.warn("Coudln't open macro file <{0}.bpm>".format(args.file))

            elif args.cmd == 'devices':
                if args.device_cmd == 'list':
                    if args.which == 'available':
                        cmd_to_send = ListAvailableDevicesCommand()
                    elif args.which == 'installed':
                        cmd_to_send = ListInstalledDevicesCommand()
                elif args.device_cmd == 'install':
                    if args.install_hwtype == 'temperature_sensor':
                        device_function = {'beer': DeviceFunction.BEER_TEMP,
                                           'room': DeviceFunction.ROOM_TEMP,
                                           'chamber': DeviceFunction.CHAMBER_TEMP}[args.function]

                        if (device_function == DeviceFunction.BEER_TEMP):
                            assigned_to = DeviceAssignation.BEER
                        else:
                            assigned_to = DeviceAssignation.CHAMBER

                        cmd_to_send = InstallDeviceCommand(slot=args.slot_id,
                                                           hardware_type=HardwareType.TEMP_SENSOR,
                                                           assigned_to=assigned_to,
                                                           address=args.address,
                                                           function=device_function)
                    elif args.install_hwtype == 'heater':
                        cmd_to_send = InstallDeviceCommand(slot=args.slot_id,
                                                           hardware_type=HardwareType.DIGITAL_PIN,
                                                           assigned_to_beer=False,
                                                           assigned_to_chamber=True,
                                                           pin=args.pin,
                                                           function=DeviceFunction.CHAMBER_HEATER)
                    elif args.install_hwtype == 'cooler':
                        cmd_to_send = InstallDeviceCommand(slot=args.slot_id,
                                                           hardware_type=HardwareType.DIGITAL_PIN,
                                                           assigned_to_beer=False,
                                                           assigned_to_chamber=True,
                                                           pin=args.pin,
                                                           function=DeviceFunction.CHAMBER_COOLER)

                elif args.device_cmd == 'uninstall':
                    cmd_to_send = UninstallDeviceCommand(slot=args.slot_id)

        if cmd_to_send is not None:
            from construct.lib import hexlify
            import codecs
            cli.raw_msg_logger.info("> {0}".format(hexlify(cmd_to_send)))
            self.app.controller.write(codecs.encode(cmd_to_send, "hex"))
            self.app.controller.write(b"\n")

        buffer.reset(append_to_history=True)


        return True

from brewpiv2.constants import (
    DeviceFunction,
    DeviceType,
    HardwareType
)

class UIMessageHandler:
    def __init__(self, cli):
        self.cli = cli
        self.app = cli.app
        super()

    def available_device(self, anAvailableDeviceMessage):
        if anAvailableDeviceMessage.hardware_type == HardwareType.TEMP_SENSOR:
            self.cli.logger.info("~ Temperature Sensor 1-wire@{0}".format(anAvailableDeviceMessage.address))
        elif anAvailableDeviceMessage.hardware_type == HardwareType.DIGITAL_PIN:
            self.cli.logger.info("~ Digital Pin at {0}".format(anAvailableDeviceMessage.pin))
        else:
            self.cli.logger.info("Unknown available device {0}".format(anAvailableDeviceMessage))

    def installed_device(self, anInstalledDeviceMessage):
        if anInstalledDeviceMessage.device_type == DeviceType.TEMP_SENSOR:
            self.cli.logger.info("[{0}] Temperature Sensor 1-wire @{1}".format(anInstalledDeviceMessage.slot,
                                                                          anInstalledDeviceMessage.address))
        elif anInstalledDeviceMessage.device_type == DeviceType.PWM_ACTUATOR:
            if anInstalledDeviceMessage.function == DeviceFunction.CHAMBER_HEATER:
                self.cli.logger.info("[{0}] Chamber Heater on pin {1}".format(anInstalledDeviceMessage.slot,
                                                                              anInstalledDeviceMessage.pin))
            elif anInstalledDeviceMessage.function == DeviceFunction.CHAMBER_COOLER:
                self.cli.logger.info("[{0}] Chamber Cooler on pin {1}".format(anInstalledDeviceMessage.slot,
                                                                              anInstalledDeviceMessage.pin))


        else:
            self.cli.logger.info("[{0}] Unknow installed device".format(anInstalledDeviceMessage.slot))

    def uninstalled_device(self, anUninstalledDeviceMessage):
        self.cli.logger.info("Uninstalled device at slot {0}".format(anUninstalledDeviceMessage.slot))

    def log_message(self, aLogMessage):
        self.cli.logger.info("Read Log")

    def control_settings(self, aControlSettingsMessage):
        self.cli.logger.info("Read settings")

    def control_constants(self, aControlConstantsMessage):
        self.cli.logger.info("Read constants")

    def temperatures(self, aTemperaturesMessage):
        self.app.buffers['STATE'].reset()

        if aTemperaturesMessage.beer_setpoint:
            self.app.buffers['STATE'].insert_text("Beer Mode: {0}° -> {1}°".format(aTemperaturesMessage.beer_temp or "[not connected]",
                                                                                   aTemperaturesMessage.beer_setpoint))
        elif aTemperaturesMessage.fridge_setpoint:
            self.app.buffers['STATE'].insert_text("Fridge Mode: {0}° -> {1}°".format(aTemperaturesMessage.fridge_temp or "[not connected]",
                                                                                     aTemperaturesMessage.fridge_setpoint))
        if aTemperaturesMessage.room_temp:
            self.app.buffers['STATE'].insert_text(" | Room Temp: {0}".format(aTemperaturesMessage.room_temp))

        if aTemperaturesMessage.beer_annotation:
            self.cli.logger.info(aTemperaturesMessage.beer_annotation)

        if aTemperaturesMessage.fridge_annotation:
            self.cli.logger.info(aTemperaturesMessage.fridge_annotation)


class CboxApplication(Application):
    def get_prompt_tokens(self, cli):
        tokens = []
        if self.controller:
            tokens += [
                (Token.Name, 'Controlbox'),
                (Token.At,       '@'),
                (Token.Host,     'localhost'),
                (Token.Colon,    ':')
            ]
            if self.controller:
                tokens += [
                    (Token.IsConnected, '[OK]')
                ]
        else:
            tokens += [
                (Token.Toolbar, "No Controlbox Controller Connected."),
            ]

        tokens += [
            (Token.Pound, '> ')
        ]

        return tokens


    def __init__(self):
        self.command_parser = BrewPiCommandParser(self)

        self.buffers = {
            DEFAULT_BUFFER: Buffer(completer=command_completer, enable_history_search=True, history=InMemoryHistory(), accept_action=AcceptAction(self.command_parser.parse)),
            'MESSAGES': Buffer(),
            'RESULT': Buffer(),
            'STATE': Buffer(),
        }

        self.registry = load_key_bindings()
        self.registry.add_binding(Keys.ControlC, eager=True)(self._on_request_shutdown)
        self.registry.add_binding(Keys.ControlQ, eager=True)(self._on_request_shutdown)


        self.layout = HSplit([
            # One window that holds the BufferControl with the default buffer on the
            # left.
            VSplit([
                HSplit([
                    Window(content=TokenListControl(get_tokens=lambda cli: [(Token.Title, 'Command Result')]), height=D.exact(1)),
                    Window(content=BufferControl(buffer_name='RESULT'),
                           wrap_lines=True,
                           left_margins=[ScrollbarMargin()]),
                ]),

                Window(width=D.exact(1), content=FillControl('|', token=Token.Line)),
                HSplit([
                    Window(content=TokenListControl(get_tokens=lambda cli: [(Token.Title, 'Raw Protocol Messages')]), height=D.exact(1)),
                    Window(content=BufferControl(buffer_name='MESSAGES', lexer=PygmentsLexer(JsonLexer)),
                           wrap_lines=True,
                           left_margins=[NumberredMargin()],
                           right_margins=[ScrollbarMargin()])
                ])

            ]),

            VSplit([
                Window(content=TokenListControl(get_tokens=self.get_prompt_tokens), height=D.exact(1), dont_extend_width=True),
                Window(content=BufferControl(buffer_name=DEFAULT_BUFFER), height=D.exact(1), dont_extend_height=True),
            ]),
            Window(content=BufferControl(buffer_name='STATE'), height=D.exact(1), dont_extend_height=True)
        ])

        super().__init__(layout=self.layout,
                         buffers=self.buffers,
                         key_bindings_registry=self.registry,
                         mouse_support=True,
                         style=style_from_pygments(get_style_by_name('emacs'),
                                                   style_dict={
                                                       Token.Toolbar: '#ffffff bg:#333333',
                                                       Token.Title: '#ffffff bg:#000088',
                                                       # User input.
                                                       Token:          '#ff0066',

                                                       # Prompt.
                                                       Token.Name: '#884444 italic',
                                                       Token.At:       '#00aa00',
                                                       Token.Colon:    '#00aa00',
                                                       Token.Pound:    '#00aa00',
                                                       Token.Host:     '#000088 bg:#aaaaff',
                                                       Token.Path:     '#884444 underline',
                                                       # Make a selection reverse/underlined.
                                                       # (Use Control-Space to select.)
                                                       Token.SelectedText: 'reverse underline',
                                                   }),
                         use_alternate_screen=True)


        # BrewPi Stuff
        self.controller = None


    def _on_request_shutdown(self, event):
        """
        Pressing Ctrl-Q or Ctrl-C will exit the user interface.
        Setting a return value means: quit the event loop that drives the user
        interface and return this value from the `CommandLineInterface.run()` call.
        Note that Ctrl-Q does not work on all terminals. Sometimes it requires
        executing `stty -ixon`.
        """
        event.cli.set_return_value(None)

from pygments.lexers import JsonLexer

class CboxShell(CommandLineInterface):
    def __init__(self):
        self.parser = ArgumentParser()
        self.parser.add_argument("device_uri", help="physical device (i.e. /dev/ttyACM0) or address (e.g. socket://10.1.1.1:6666)")

        self.app = CboxApplication()
        self.loop = create_eventloop()

        # Logging
        self.logger = logging.getLogger("controlbox")
        self.logger.setLevel(level=logging.INFO)
        self.logger.handlers = []

        self.logger.addHandler(ConsoleHandler(self.app.buffers['RESULT'], self))

        self.raw_msg_logger = logging.getLogger("raw-messages")
        self.raw_msg_logger.setLevel(level=logging.DEBUG)
        handler = ConsoleHandler(self.app.buffers['MESSAGES'], self)
        # handler.setFormatter(coloredlogs.ColoredFormatter('%(message)s'))
        self.raw_msg_logger.addHandler(handler)

        super().__init__(application=self.app, eventloop=self.loop)

        self.patch_stdout_context(raw=False, patch_stdout=True, patch_stderr=True)

        # self.msg_handler = UIMessageHandler(self)

    def run(self):
        args = self.parser.parse_args()

        self.loop.run_in_executor(self._listen_for_events)

        try:
            self.app.controller = serial.Serial("/dev/ttyACM0", timeout=2)

            # self.app.controller.send(ListAvailableDevicesCommand())

            super().run()
        finally:
            self.loop.close()


    def _listen_for_events(self):
        import io
        sio = io.TextIOWrapper(io.BufferedRWPair(self.app.controller, self.app.controller), newline="\r\n")

        while not self.is_returning:
            if self.app.controller:
                if self.app.controller:
                    for line in sio.readlines():
                        line = line.replace(' ', '')
                        line = line.strip("\n")
                        line = line.strip("\r")
                        import binascii
                        self.raw_msg_logger.info(line)
                        from protocol import decoder
                        response = decoder.accept(binascii.unhexlify(line))
                        self.logger.info(response)
                        self.logger.info("\n")

            time.sleep(0.1)

        self.app.controller.close()









if __name__ == "__main__":
    shell = CboxShell()
    shell.run()

    exit(0)

