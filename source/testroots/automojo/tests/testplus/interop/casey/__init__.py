
from automojo import testplus

from automojo.landscaping.factories import create_landscape, create_linux_client_coordinator_coupling

testplus.originate.originate_parameter(create_linux_client_coordinator_coupling, identifier="lc_coupling")

testplus.originate.originate_parameter(create_landscape, identifier='lscape')
