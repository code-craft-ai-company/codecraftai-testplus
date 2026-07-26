"""
    Simplecluster test suites.  Tests under this subtree run against a
    landscape of real machines, so the landscape resource is originated
    HERE -- at the scope that owns it -- and every descendant test can
    consume `lscape` (directly or through factories like `each_client`).
"""

from ccai import testplus

from ccai.landscaping.factories import create_landscape

testplus.originate.parameter(create_landscape, identifier="lscape")
