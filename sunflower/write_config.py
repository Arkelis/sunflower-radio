import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


from sunflower.core.liquidsoap import write_liquidsoap_config
from sunflower.channels import tournesol, music


if __name__ == '__main__':
    write_liquidsoap_config(tournesol, music, filename="sunflower")
