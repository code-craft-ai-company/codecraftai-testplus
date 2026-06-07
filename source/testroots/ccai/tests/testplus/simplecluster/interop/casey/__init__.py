
from ccai import testplus

from ccai.landscaping.factories import create_landscape, create_linux_client_coordinator_coupling

testplus.originate.parameter(create_linux_client_coordinator_coupling, identifier="lc_coupling")

testplus.originate.parameter(create_landscape, identifier='lscape')
