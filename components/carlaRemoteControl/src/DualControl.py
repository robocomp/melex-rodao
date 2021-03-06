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

    def __init__(self, camera_manager, hud, wheel_config, proxy):

        self.carlavehiclecontrol_proxy = proxy
        self.camera_manager = camera_manager
        self.hud = hud
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
        self.current_control = RoboCompCarlaVehicleControl.VehicleControl()
        self.prev_control = RoboCompCarlaVehicleControl.VehicleControl()
        pygame.joystick.init()

        joystick_count = pygame.joystick.get_count()
        if joystick_count > 1:
            raise ValueError("Please Connect Just One Joystick")
        elif joystick_count < 1:
            raise ValueError("Please Connect One Joystick")

        self._joystick = pygame.joystick.Joystick(0)
        self._joystick.init()

        self._parser = ConfigParser()
        self._parser.read(wheel_config)
        self._steer_idx = int(
            self._parser.get('G29 Racing Wheel', 'steering_wheel'))
        self._throttle_idx = int(
            self._parser.get('G29 Racing Wheel', 'throttle'))
        self._brake_idx = int(self._parser.get('G29 Racing Wheel', 'brake'))
        self._reverse_idx = int(self._parser.get('G29 Racing Wheel', 'reverse'))
        self._handbrake_idx = int(
            self._parser.get('G29 Racing Wheel', 'handbrake'))

    def parse_events(self, clock):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True

            ######################
            ## Joystick control##
            ####################
            elif event.type == pygame.JOYBUTTONDOWN:

                if event.button == 1:
                    self.hud.toggle_info()
                if event.button == 2:
                    self.camera_manager.toggle_camera()
                if event.button == self._handbrake_idx:
                    print('HAANDBRAKE !!!!')
                    self.handbrake_on = False if self.handbrake_on else True

                elif event.button == self._reverse_idx:
                    self._control_gear = 1 if self._control_reverse else -1

        self._parse_vehicle_keys(pygame.key.get_pressed(), clock.get_time())
        self._parse_vehicle_wheel()
        self._control_reverse = self._control_gear < 0
        self._control_hand_brake = self.handbrake_on
        if self._control_hand_brake:
            self._control_throttle = 0

    def publish_vehicle_control(self):

        time_elapsed = None

        try:
            curr_time = time.time()

            result = self.carlavehiclecontrol_proxy.updateVehicleControl(self.current_control)

            if result:
                time_elapsed = time.time() - curr_time

        except Exception as e:
            print(e)

        return self.current_control, time_elapsed

    def car_moved(self):
        self.current_control = RoboCompCarlaVehicleControl.VehicleControl()
        self.current_control.throttle = self._control_throttle
        self.current_control.steer = self._control_steer
        self.current_control.brake = self._control_brake
        self.current_control.gear = self._control_gear
        self.current_control.handbrake = self._control_hand_brake
        self.current_control.reverse = self._control_reverse
        self.current_control.manualgear = self._control_manual_gear_shift

        moved = False
        if self.current_control.throttle != self.prev_control.throttle or \
                self.current_control.steer != self.prev_control.steer or \
                self.current_control.brake != self.prev_control.brake or \
                self.current_control.gear != self.prev_control.gear or \
                self.current_control.handbrake != self.prev_control.handbrake or \
                self.current_control.reverse != self.prev_control.reverse or \
                self.current_control.manualgear != self.prev_control.manualgear:
            moved = True

        self.prev_control = self.current_control
        return moved

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
        jsButtons = [float(self._joystick.get_button(i)) for i in
                     range(self._joystick.get_numbuttons())]

        K1 = 0.55
        steerCmd = K1 * math.tan(1.1 * jsInputs[self._steer_idx])

        K2 = 1.6
        throttleCmd = K2 + (2.05 * math.log10(
            -0.7 * jsInputs[self._throttle_idx] + 1.4) - 1.2) / 0.92
        if throttleCmd <= 0:
            throttleCmd = 0
        elif throttleCmd > 1:
            throttleCmd = 1

        brakeCmd = 1.6 + (2.05 * math.log10(
            -0.7 * jsInputs[self._brake_idx] + 1.4) - 1.2) / 0.92
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
