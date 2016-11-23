from machinekit import hal
from machinekit import rtapi as rt
from machinekit import config as c

from fdm.config import base


def hardware_read():
    hal.addf('hpg.capture-position', 'servo-thread')
    hal.addf('bb_gpio.read', 'servo-thread')


def hardware_write():
    hal.addf('hpg.update', 'servo-thread')
    hal.addf('bb_gpio.write', 'servo-thread')


def init_hardware():
    watchList = []

    # load low-level drivers
    rt.loadrt('hal_bb_gpio', output_pins='807,826,917,918,924,926', input_pins='808,809,810,814,817,818')
    prubin = '%s/%s' % (c.Config().EMC2_RTLIB_DIR, c.find('PRUCONF', 'PRUBIN'))
    rt.loadrt(c.find('PRUCONF', 'DRIVER'),
              pru=0, num_stepgens=6, num_pwmgens=6,
              prucode=prubin, halname='hpg')

    # Python user-mode HAL module to read ADC value and generate a thermostat output for PWM
    defaultThermistor = 'semitec_103GT_2'
    hal.loadusr('hal_temp_bbb',
                name='temp',
                interval=0.05,
                filter_size=1,
                cape_board='CRAMPS',
                channels='04:%s,05:%s,02:%s,03:%s'
                % (c.find('HBP', 'THERMISTOR', defaultThermistor),
                   c.find('EXTRUDER_0', 'THERMISTOR', defaultThermistor),
                   c.find('EXTRUDER_1', 'THERMISTOR', defaultThermistor),
                   c.find('EXTRUDER_2', 'THERMISTOR', defaultThermistor)),
                wait_name='temp')
    watchList.append(['temp', 0.1])

    base.usrcomp_status('temp', 'temp-hw', thread='servo-thread')
    base.usrcomp_watchdog(watchList, 'estop-reset', thread='servo-thread',
                          errorSignal='watchdog-error')


def setup_hardware(thread):
    # PWM
    hal.Pin('hpg.pwmgen.00.pwm_period').set(10000000)  # 100Hz
    hal.Pin('hpg.pwmgen.00.out.00.pin').set(813)
    hal.Pin('hpg.pwmgen.00.out.01.pin').set(819)
    hal.Pin('hpg.pwmgen.00.out.02.pin').set(914)
    #hal.Pin('hpg.pwmgen.00.out.03.pin').set(921)
    #hal.Pin('hpg.pwmgen.00.out.04.pin').set(941)
    #hal.Pin('hpg.pwmgen.00.out.05.pin').set(922)
    # HBP
    hal.Pin('hpg.pwmgen.00.out.00.enable').set(True)
    hal.Pin('hpg.pwmgen.00.out.00.value').link('hbp-temp-pwm')
    # configure extruders
    for n in range(0, 3):
        hal.Pin('hpg.pwmgen.00.out.%02i.enable' % (n + 1)).set(True)
        hal.Pin('hpg.pwmgen.00.out.%02i.value' % (n + 1)).link('e%i-temp-pwm' % n)
    # configure fans
    for n in range(0, 1):
        hal.Pin('hpg.pwmgen.00.out.%02i.enable' % (n + 4)).link('f%i-pwm-enable' % n)
        hal.Pin('hpg.pwmgen.00.out.%02i.value' % (n + 4)).link('f%i-pwm' % n)
        hal.Signal('f%i-pwm-enable' % n).set(True)

    # configure hotend cooling fan
    hal.Pin('hpg.pwmgen.00.out.05.enable').link('exp0-pwm-enable')
    hal.Pin('hpg.pwmgen.00.out.05.value').set(1.0)
    hal.Pin('hpg.pwmgen.00.out.05.value').link('exp0-pwm')
    # configure leds
    # none

    # GPIO
    hal.Pin('bb_gpio.p8.in-08').link('limit-0-home')   # X
    hal.Pin('bb_gpio.p8.in-09').link('limit-0-min')    # X
    hal.Pin('bb_gpio.p8.in-10').link('limit-1-home')   # Y
    hal.Pin('bb_gpio.p8.in-14').link('limit-1-min')    # Y
    hal.Pin('bb_gpio.p8.in-17').link('limit-2-home')   # Z
    hal.Pin('bb_gpio.p8.in-18').link('limit-2-min')    # Z
    # probe ...

    # Adjust as needed for your switch polarity
    hal.Pin('bb_gpio.p8.in-08.invert').set(False)
    hal.Pin('bb_gpio.p8.in-09.invert').set(False)
    hal.Pin('bb_gpio.p8.in-10.invert').set(False)
    hal.Pin('bb_gpio.p8.in-14.invert').set(False)
    hal.Pin('bb_gpio.p8.in-17.invert').set(False)
    hal.Pin('bb_gpio.p8.in-18.invert').set(False)

    # ADC
    hal.Pin('temp.ch-04.value').link('hbp-temp-meas')
    hal.Pin('temp.ch-05.value').link('e0-temp-meas')
    hal.Pin('temp.ch-02.value').link('e1-temp-meas')
    hal.Pin('temp.ch-03.value').link('e2-temp-meas')

    # Stepper
    hal.Pin('hpg.stepgen.00.steppin').set(812)
    hal.Pin('hpg.stepgen.00.dirpin').set(811)
    hal.Pin('hpg.stepgen.01.steppin').set(816)
    hal.Pin('hpg.stepgen.01.dirpin').set(815)
    hal.Pin('hpg.stepgen.02.steppin').set(915)
    hal.Pin('hpg.stepgen.02.dirpin').set(923)
    hal.Pin('hpg.stepgen.03.steppin').set(922)
    hal.Pin('hpg.stepgen.03.dirpin').set(921)
    #hal.Pin('hpg.stepgen.04.steppin').set(917)
    #hal.Pin('hpg.stepgen.04.dirpin').set(918)
    #hal.Pin('hpg.stepgen.05.steppin').set(924)
    #hal.Pin('hpg.stepgen.05.dirpin').set(926)

    # machine power
    #hal.Pin('bb_gpio.p8.out-07').link('emcmot-0-enable')
    #hal.Pin('bb_gpio.p9.out-23.invert').set(True)
    # Monitor estop input from hardware
    #hal.Pin('bb_gpio.p8.in-07').link('estop-in')
    #hal.Pin('bb_gpio.p8.in-07.invert').set(True)
    # drive estop-sw
    hal.Pin('bb_gpio.p8.out-07').link('estop-out')
    hal.Pin('bb_gpio.p8.out-07.invert').set(True)

    # Tie machine power signal to the Parport Cape LED
    # Feel free to tie any other signal you like to the LED
    #hal.Pin('bb_gpio.p9.out-25').link('emcmot-0-enable')
    # hal.Pin('bb_gpio.p9.out-25.invert').set(True)

    # link emcmot.xx.enable to stepper driver enable signals
    hal.Pin('bb_gpio.p9.out-26').link('emcmot-0-enable')
    hal.Pin('bb_gpio.p9.out-26.invert').set(True)

def setup_exp(name):
    hal.newsig('%s-pwm' % name, hal.HAL_FLOAT, init=0.0)
    hal.newsig('%s-pwm-enable' % name, hal.HAL_BIT, init=False)
