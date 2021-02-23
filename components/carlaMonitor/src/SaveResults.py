import csv
import os
import time
from datetime import datetime


class SaveResults:
    def __init__(self):
        self.dict_headers = {
            'gnss': ['Time', 'Latitude', 'Longitude', 'Altitude'],
            'imu': ['Time', 'Accelerometer', 'Gyroscope', 'Compass']

        }
        # Create directory to store the results
        results_directory = '/home/robocomp/robocomp/components/melex-rodao/files/results'
        if not os.path.isdir(results_directory):
            os.mkdir(results_directory)
        date = datetime.strftime(datetime.now(), "%y%m%d_%H%M")  # %S
        self.directory = os.path.join(results_directory, "test_" + date)

        if not os.path.isdir(self.directory):
            os.mkdir(self.directory)

    def save_data(self, sensor_name, data_list):
        file_name = sensor_name + '.csv'
        file_dir = os.path.join(self.directory, file_name)

        if not os.path.isfile(file_dir):
            with open(file_dir, 'w') as csvFile:
                writer = csv.writer(csvFile, delimiter=';')
                writer.writerow(
                    self.dict_headers[sensor_name])
            csvFile.close()
        with open(file_dir, 'a') as csvFile:
            writer = csv.writer(csvFile, delimiter=';')
            writer.writerow(data_list)
        csvFile.close()
