'''
Created on Jan 12, 2015

@author: Stian Sandve
'''

from sonar import Sonar
import time

def main():
    sonar = Sonar()
    
    try:
        while True:
            sonar.send_version()
            sonar.version_data()
            time.sleep(0.2)
    except KeyboardInterrupt:
        sonar.close()

if __name__ == '__main__':
    main()