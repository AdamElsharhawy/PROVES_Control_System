import time
import board
import busio
import math
import csv
import adafruit_pca9685
import adafruit_tca9548a
import adafruit_veml7700
import adafruit_drv2605
import ina219

# Initialize I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize PCA9685
pca = adafruit_pca9685.PCA9685(i2c, address=0x56)
pca.frequency = 60
pca.channels[0].duty_cycle = 0xffff
pca.channels[1].duty_cycle = 0xffff

# Initialize TCA9548A multiplexer
tca = adafruit_tca9548a.TCA9548A(i2c, address=0x77)

# Initialize VEML7700 sensors on TCA channels
veml0 = adafruit_veml7700.VEML7700(tca[0])
veml1 = adafruit_veml7700.VEML7700(tca[1])

# Initialize DRV2605
drv0 = adafruit_drv2605.DRV2605(tca[0])
try:
    drv1 = adafruit_drv2605.DRV2605(tca[1])
except:
    drv1 = adafruit_drv2605.DRV2605(tca[1], address=0x5f)

drv0.sequence[0] = adafruit_drv2605.Effect(47)
drv1.sequence[0] = adafruit_drv2605.Effect(47)

# Initialize INA219
ina = ina219.INA219(tca[5], addr=0x40)

def get_normalized_light(sensor):
    """Get normalized light reading from 0 to 1."""
    lux = sensor.lux
    # Assuming max detectable light is 120,000 lux (full sunlight)
    return min(lux / 120000, 1)

def calculate_sun_vector(x, y, z):
    """Calculate sun vector from normalized light readings."""
    magnitude = math.sqrt(x*x + y*y + z*z)
    if magnitude == 0:
        return (0, 0, 0)
    return (x/magnitude, y/magnitude, z/magnitude)

def main():
    with open('sun_vectors.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Time', 'X', 'Y', 'Z', 'Zenith Angle', 'Azimuth Angle'])

        start_time = time.time()
        while time.time() - start_time < 30:
            drv0.play()
            drv1.play()

            # Read normalized light from sensors
            x = get_normalized_light(veml0)
            y = get_normalized_light(veml1)
            z = get_normalized_light(veml1) * 0.8  # Simulate less light on Z axis

            sun_vector = calculate_sun_vector(x, y, z)

            # Calculate angle from Z-axis (zenith angle) and azimuth
            zenith = math.acos(sun_vector[2]) * 180 / math.pi
            azimuth = math.atan2(sun_vector[1], sun_vector[0]) * 180 / math.pi
            
            current_time = time.time() - start_time

            writer.writerow([current_time, sun_vector[0], sun_vector[1], sun_vector[2], zenith, azimuth])

            print("Normalized light readings:")
            print(f"X: {x:.2f}, Y: {y:.2f}, Z: {z:.2f}")
            print(f"Estimated sun vector: [{sun_vector[0]:.2f}, {sun_vector[1]:.2f}, {sun_vector[2]:.2f}]")
            print(f"Zenith angle: {zenith:.2f} degrees")
            print(f"Azimuth angle: {azimuth:.2f} degrees")
            print()
            
            print("INA219: {:6.3f}V, {:7.4}mA, {:8.5}mW".format(ina.bus_voltage, ina.current, ina.power))

            time.sleep(1)
            drv0.stop()
            drv1.stop()
            time.sleep(1)

if __name__ == "__main__":
    main()
