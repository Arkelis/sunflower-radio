from sunflower.core.liquidsoap import write_liquidsoap_config
from sunflower.channels import channels


write_liquidsoap_config(channels, filename="sunflower")
