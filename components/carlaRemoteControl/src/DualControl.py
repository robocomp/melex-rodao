import pygame
import math
import sys
import time

if sys.version_info >= (3, 0):
    from configparser import ConfigParser
else:
    from ConfigParser import RawConfigParser as ConfigParser

try:
    import pygame
    from pygame.locals import KMOD_CTRL
    from pygame.locals import KMOD_SHIFT
    from pygame.locals import K_0
    from pygame.locals import K_9
    from pygame.locals import K_BACKQUOTE
    from pygame.locals import K_BACKSPACE
    from pygame.locals import K_COMMA
    from pygame.locals import K_DOWN
    from pygame.locals import K_ESCAPE
    from pygame.locals import K_F1
    from pygame.locals import K_LEFT
    from pygame.locals import K_PERIOD
    from pygame.locals import K_RIGHT
    from pygame.locals import K_SLASH
    from pygame.locals import K_SPACE
    from pygame.locals import K_TAB
    from pygame.locals import K_UP
    from pygame.locals import K_a
    from pygame.locals import K_c
    from pygame.locals import K_d
    from pygame.locals import K_h
    from pygame.locals import K_m
    from pygame.locals import K_p
    from pygame.locals import K_q
    from pygame.locals import K_r
    from pygame.locals import K_s
    from pygame.locals import K_w
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')

import RoboCompCarlaVehicleControl


# ==============================================================================
# -- DualControl -----------------------------------------------------------
# ==============================================================================


class DualControl(object):
    def __init__(self, camera_manager, hud, proxy):
    # def __init__(self, camera_manager, proxy):
        self.carlavehiclecontrol_proxy = proxy
        self.camera_manager = camera_manager
        self.hud = hud
        self.contFPS = 0
        self.start = time.time()

        self._autopilot_enabled = False
        self._steer_cache = 0.0
        self._control_gear = 0
        self._control_throttle = 0.0
        self._control_steer = 0.0
        self._control_brake = 0.0
        self._control_gear = 0.0
        self._control_hand_brake = False
        self._control_reverse = False
        self.handbrake_on = False
        self._control_manual_gear_shift = False

        # initialize steering wheel
        pygame.joystick.init()

        joystick_count = pygame.joystick.get_count()
        if joystick_count > 1:
            raise ValueError("Please Connect Just One Joystick")

        self._joystick = pygame.joystick.Joystick(0)
        self._joystick.init()

        self._parser = ConfigParser()
        self._parser.read("/home/robocomp/robocomp/components/melex-rodao/files/carla/wheel_config.ini")
        self._steer_idx = int(
            self._parser.get('G29 Racing Wheel', 'steering_wheel'))
        self._throttle_idx = int(
            self._parser.get('G29 Racing Wheel', 'throttle'))
        self._brake_idx = int(self._parser.get('G29 Racing Wheel', 'brake'))
        self._reverse_idx = int(self._parser.get('G29 Racing Wheel', 'reverse'))
        self._handbrake_idx = int(
            self._parser.get('G29 Racing Wheel', 'handbrake'))

    # def parse_events(self, world, clock):
    def parse_events(self, clock):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True

            ######################
            ## Joystick control##
            ####################
            elif event.type == pygame.JOYBUTTONDOWN:
                # if event.button == 0:
                #     world.restart()
                if event.button == 1:
                    self.hud.toggle_info()
                if event.button == 2:
                    self.camera_manager.toggle_camera()
                # elif event.button == 3:
                #     world.next_weather()

                if event.button == self._handbrake_idx:
                    print('HAANDBRAKE !!!!')
                    self.handbrake_on = False if self.handbrake_on else True

                elif event.button == self._reverse_idx:
                    self._control_gear = 1 if self._control_reverse else -1
                # elif event.button == 23:
                #     print('Next sensors pressed')
                #     world.camera_manager.next_sensor()

            ######################
            ## Keyboard control ##
            ######################
            elif event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    return True
                # elif event.key == K_BACKSPACE:
                #     world.restart()
                # elif event.key == K_F1:
                #     world.hud.toggle_info()
                # elif event.key == K_h or (event.key == K_SLASH and pygame.key.get_mods() & KMOD_SHIFT):
                #     world.hud.help.toggle()
                # elif event.key == K_TAB:
                #     world.camera_manager.toggle_camera()
                # elif event.key == K_c and pygame.key.get_mods() & KMOD_SHIFT:
                #     world.next_weather(reverse=True)
                # elif event.key == K_c:
                #     world.next_weather()
                # elif event.key == K_BACKQUOTE:
                #     world.camera_manager.next_sensor()
                # elif K_0 < event.key <= K_9:
                #     world.camera_manager.set_sensor(event.key - 1 - K_0)
                # elif event.key == K_r:
                #     world.camera_manager.toggle_recording()

                if event.key == K_q:
                    self._control_gear = 1 if self._control_reverse else -1
                elif event.key == K_m:
                    self._control_manual_gear_shift = not self._control_manual_gear_shift
                    # self._control_gear = world.player.get_control().gear
                    self._control_gear = 1
                    # world.hud.notification('%s Transmission' %
                    #                        ('Manual' if self._control_manual_gear_shift else 'Automatic'))
                elif self._control_manual_gear_shift and event.key == K_COMMA:
                    self._control_gear = max(-1, self._control_gear - 1)
                elif self._control_manual_gear_shift and event.key == K_PERIOD:
                    self._control_gear = self._control_gear + 1
                elif event.key == K_p:
                    self._autopilot_enabled = not self._autopilot_enabled
                    # world.player.set_autopilot(self._autopilot_enabled)
                    # world.hud.notification('Autopilot %s' % ('On' if self._autopilot_enabled else 'Off'))

        if not self._autopilot_enabled:
            self._parse_vehicle_keys(pygame.key.get_pressed(), clock.get_time())
            self._parse_vehicle_wheel()
            self._control_reverse = self._control_gear < 0
            self._control_hand_brake = self.handbrake_on
            if self._control_hand_brake:
                self._control_throttle = 0


    def publish_vehicle_control(self):
        control = RoboCompCarlaVehicleControl.VehicleControl()
        control.throttle = self._control_throttle
        control.steer = self._control_steer
        control.brake = self._control_brake
        control.gear = self._control_gear
        control.handbrake = self._control_hand_brake
        control.reverse = self._control_reverse
        control.manualgear = self._control_manual_gear_shift


        try:
            self.carlavehiclecontrol_proxy.updateVehicleControl(control)

        except Exception as e:
            print(e)

        return control

    def _parse_vehicle_keys(self, keys, milliseconds):
        self._control_throttle = 1.0 if keys[K_UP] or keys[K_w] else 0.0
        steer_increment = 5e-4 * milliseconds
        if keys[K_LEFT] or keys[K_a]:
            self._steer_cache -= steer_increment
        elif keys[K_RIGHT] or keys[K_d]:
            self._steer_cache += steer_increment
        else:
            self._steer_cache = 0.0
        self._steer_cache = min(0.7, max(-0.7, self._steer_cache))
        self._control_steer = round(self._steer_cache, 1)
        self._control_brake = 1.0 if keys[K_DOWN] or keys[K_s] else 0.0
        self._control_hand_brake = keys[K_SPACE]

    def _parse_vehicle_wheel(self):
        numAxes = self._joystick.get_numaxes()
        jsInputs = [float(self._joystick.get_axis(i)) for i in range(numAxes)]
        # print (jsInputs)
        jsButtons = [float(self._joystick.get_button(i)) for i in
                     range(self._joystick.get_numbuttons())]

        # Custom function to map range of inputs [1, -1] to outputs [0, 1] i.e 1 from inputs means nothing is pressed
        # For the steering, it seems fine as it is

        K1 = 0.55  # 0.55
        steerCmd = K1 * math.tan(1.1 * jsInputs[self._steer_idx])

        K2 = 1.6  # 1.6
        throttleCmd = K2 + (2.05 * math.log10(
            -0.7 * jsInputs[self._throttle_idx] + 1.4) - 1.2) / 0.75
        if throttleCmd <= 0:
            throttleCmd = 0
        elif throttleCmd > 1:
            throttleCmd = 1

        brakeCmd = 1.6 + (2.05 * math.log10(
            -0.7 * -jsInputs[self._brake_idx] + 1.4) - 1.2) / 0.92
        if brakeCmd <= 0:
            brakeCmd = 0
        elif brakeCmd > 1:
            brakeCmd = 1

        self._control_steer = steerCmd
        self._control_brake = brakeCmd
        self._control_throttle = throttleCmd


    @staticmethod
    def _is_quit_shortcut(key):
        return (key == K_ESCAPE) or (key == K_q and pygame.key.get_mods() & KMOD_CTRL)
