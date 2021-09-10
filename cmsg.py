__filename__ = "cmsg.py"
__author__ = "Bob Mottram"
__credits__ = ["Bartek Radwanski"]
__license__ = "AGPL3+"
__version__ = "1.0.0"
__maintainer__ = "Bob Mottram"
__email__ = "bob@libreserver.org"
__status__ = "Production"
__module_group__ = "Core"

import re
dict = {
    '<f0>': "\u001b[38;5;0m",
    '<f1>': "\u001b[38;5;1m",
    '<f2>': "\u001b[38;5;2m",
    '<f3>': "\u001b[38;5;3m",
    '<f4>': "\u001b[38;5;4m",
    '<f5>': "\u001b[38;5;5m",
    '<f6>': "\u001b[38;5;6m",
    '<f7>': "\u001b[38;5;7m",
    '<f8>': "\u001b[38;5;8m",
    '<f9>': "\u001b[38;5;9m",
    '<f10>': "\u001b[38;5;10m",
    '<f11>': "\u001b[38;5;11m",
    '<f12>': "\u001b[38;5;12m",
    '<f13>': "\u001b[38;5;13m",
    '<f14>': "\u001b[38;5;14m",
    '<f15>': "\u001b[38;5;15m",
    '<f16>': "\u001b[38;5;16m",
    '<f17>': "\u001b[38;5;17m",
    '<f18>': "\u001b[38;5;18m",
    '<f19>': "\u001b[38;5;19m",
    '<f20>': "\u001b[38;5;20m",
    '<f21>': "\u001b[38;5;21m",
    '<f22>': "\u001b[38;5;22m",
    '<f23>': "\u001b[38;5;23m",
    '<f24>': "\u001b[38;5;24m",
    '<f25>': "\u001b[38;5;25m",
    '<f26>': "\u001b[38;5;26m",
    '<f27>': "\u001b[38;5;27m",
    '<f28>': "\u001b[38;5;28m",
    '<f29>': "\u001b[38;5;29m",
    '<f30>': "\u001b[38;5;30m",
    '<f31>': "\u001b[38;5;31m",
    '<f32>': "\u001b[38;5;32m",
    '<f33>': "\u001b[38;5;33m",
    '<f34>': "\u001b[38;5;34m",
    '<f35>': "\u001b[38;5;35m",
    '<f36>': "\u001b[38;5;36m",
    '<f37>': "\u001b[38;5;37m",
    '<f38>': "\u001b[38;5;38m",
    '<f39>': "\u001b[38;5;39m",
    '<f40>': "\u001b[38;5;40m",
    '<f41>': "\u001b[38;5;41m",
    '<f42>': "\u001b[38;5;42m",
    '<f43>': "\u001b[38;5;43m",
    '<f44>': "\u001b[38;5;44m",
    '<f45>': "\u001b[38;5;45m",
    '<f46>': "\u001b[38;5;46m",
    '<f47>': "\u001b[38;5;47m",
    '<f48>': "\u001b[38;5;48m",
    '<f49>': "\u001b[38;5;49m",
    '<f50>': "\u001b[38;5;50m",
    '<f51>': "\u001b[38;5;51m",
    '<f52>': "\u001b[38;5;52m",
    '<f53>': "\u001b[38;5;53m",
    '<f54>': "\u001b[38;5;54m",
    '<f55>': "\u001b[38;5;55m",
    '<f56>': "\u001b[38;5;56m",
    '<f57>': "\u001b[38;5;57m",
    '<f58>': "\u001b[38;5;58m",
    '<f59>': "\u001b[38;5;59m",
    '<f60>': "\u001b[38;5;60m",
    '<f61>': "\u001b[38;5;61m",
    '<f62>': "\u001b[38;5;62m",
    '<f63>': "\u001b[38;5;63m",
    '<f64>': "\u001b[38;5;64m",
    '<f65>': "\u001b[38;5;65m",
    '<f66>': "\u001b[38;5;66m",
    '<f67>': "\u001b[38;5;67m",
    '<f68>': "\u001b[38;5;68m",
    '<f69>': "\u001b[38;5;69m",
    '<f70>': "\u001b[38;5;70m",
    '<f71>': "\u001b[38;5;71m",
    '<f72>': "\u001b[38;5;72m",
    '<f73>': "\u001b[38;5;73m",
    '<f74>': "\u001b[38;5;74m",
    '<f75>': "\u001b[38;5;75m",
    '<f76>': "\u001b[38;5;76m",
    '<f77>': "\u001b[38;5;77m",
    '<f78>': "\u001b[38;5;78m",
    '<f79>': "\u001b[38;5;79m",
    '<f80>': "\u001b[38;5;80m",
    '<f81>': "\u001b[38;5;81m",
    '<f82>': "\u001b[38;5;82m",
    '<f83>': "\u001b[38;5;83m",
    '<f84>': "\u001b[38;5;84m",
    '<f85>': "\u001b[38;5;85m",
    '<f86>': "\u001b[38;5;86m",
    '<f87>': "\u001b[38;5;87m",
    '<f88>': "\u001b[38;5;88m",
    '<f89>': "\u001b[38;5;89m",
    '<f90>': "\u001b[38;5;90m",
    '<f91>': "\u001b[38;5;91m",
    '<f92>': "\u001b[38;5;92m",
    '<f93>': "\u001b[38;5;93m",
    '<f94>': "\u001b[38;5;94m",
    '<f95>': "\u001b[38;5;95m",
    '<f96>': "\u001b[38;5;96m",
    '<f97>': "\u001b[38;5;97m",
    '<f98>': "\u001b[38;5;98m",
    '<f99>': "\u001b[38;5;99m",
    '<f100>': "\u001b[38;5;100m",
    '<f101>': "\u001b[38;5;101m",
    '<f102>': "\u001b[38;5;102m",
    '<f103>': "\u001b[38;5;103m",
    '<f104>': "\u001b[38;5;104m",
    '<f105>': "\u001b[38;5;105m",
    '<f106>': "\u001b[38;5;106m",
    '<f107>': "\u001b[38;5;107m",
    '<f108>': "\u001b[38;5;108m",
    '<f109>': "\u001b[38;5;109m",
    '<f110>': "\u001b[38;5;110m",
    '<f111>': "\u001b[38;5;111m",
    '<f112>': "\u001b[38;5;112m",
    '<f113>': "\u001b[38;5;113m",
    '<f114>': "\u001b[38;5;114m",
    '<f115>': "\u001b[38;5;115m",
    '<f116>': "\u001b[38;5;116m",
    '<f117>': "\u001b[38;5;117m",
    '<f118>': "\u001b[38;5;118m",
    '<f119>': "\u001b[38;5;119m",
    '<f120>': "\u001b[38;5;120m",
    '<f121>': "\u001b[38;5;121m",
    '<f122>': "\u001b[38;5;122m",
    '<f123>': "\u001b[38;5;123m",
    '<f124>': "\u001b[38;5;124m",
    '<f125>': "\u001b[38;5;125m",
    '<f126>': "\u001b[38;5;126m",
    '<f127>': "\u001b[38;5;127m",
    '<f128>': "\u001b[38;5;128m",
    '<f129>': "\u001b[38;5;129m",
    '<f130>': "\u001b[38;5;130m",
    '<f131>': "\u001b[38;5;131m",
    '<f132>': "\u001b[38;5;132m",
    '<f133>': "\u001b[38;5;133m",
    '<f134>': "\u001b[38;5;134m",
    '<f135>': "\u001b[38;5;135m",
    '<f136>': "\u001b[38;5;136m",
    '<f137>': "\u001b[38;5;137m",
    '<f138>': "\u001b[38;5;138m",
    '<f139>': "\u001b[38;5;139m",
    '<f140>': "\u001b[38;5;140m",
    '<f141>': "\u001b[38;5;141m",
    '<f142>': "\u001b[38;5;142m",
    '<f143>': "\u001b[38;5;143m",
    '<f144>': "\u001b[38;5;144m",
    '<f145>': "\u001b[38;5;145m",
    '<f146>': "\u001b[38;5;146m",
    '<f147>': "\u001b[38;5;147m",
    '<f148>': "\u001b[38;5;148m",
    '<f149>': "\u001b[38;5;149m",
    '<f150>': "\u001b[38;5;150m",
    '<f151>': "\u001b[38;5;151m",
    '<f152>': "\u001b[38;5;152m",
    '<f153>': "\u001b[38;5;153m",
    '<f154>': "\u001b[38;5;154m",
    '<f155>': "\u001b[38;5;155m",
    '<f156>': "\u001b[38;5;156m",
    '<f157>': "\u001b[38;5;157m",
    '<f158>': "\u001b[38;5;158m",
    '<f159>': "\u001b[38;5;159m",
    '<f160>': "\u001b[38;5;160m",
    '<f161>': "\u001b[38;5;161m",
    '<f162>': "\u001b[38;5;162m",
    '<f163>': "\u001b[38;5;163m",
    '<f164>': "\u001b[38;5;164m",
    '<f165>': "\u001b[38;5;165m",
    '<f166>': "\u001b[38;5;166m",
    '<f167>': "\u001b[38;5;167m",
    '<f168>': "\u001b[38;5;168m",
    '<f169>': "\u001b[38;5;169m",
    '<f170>': "\u001b[38;5;170m",
    '<f171>': "\u001b[38;5;171m",
    '<f172>': "\u001b[38;5;172m",
    '<f173>': "\u001b[38;5;173m",
    '<f174>': "\u001b[38;5;174m",
    '<f175>': "\u001b[38;5;175m",
    '<f176>': "\u001b[38;5;176m",
    '<f177>': "\u001b[38;5;177m",
    '<f178>': "\u001b[38;5;178m",
    '<f179>': "\u001b[38;5;179m",
    '<f180>': "\u001b[38;5;180m",
    '<f181>': "\u001b[38;5;181m",
    '<f182>': "\u001b[38;5;182m",
    '<f183>': "\u001b[38;5;183m",
    '<f184>': "\u001b[38;5;184m",
    '<f185>': "\u001b[38;5;185m",
    '<f186>': "\u001b[38;5;186m",
    '<f187>': "\u001b[38;5;187m",
    '<f188>': "\u001b[38;5;188m",
    '<f189>': "\u001b[38;5;189m",
    '<f190>': "\u001b[38;5;190m",
    '<f191>': "\u001b[38;5;191m",
    '<f192>': "\u001b[38;5;192m",
    '<f193>': "\u001b[38;5;193m",
    '<f194>': "\u001b[38;5;194m",
    '<f195>': "\u001b[38;5;195m",
    '<f196>': "\u001b[38;5;196m",
    '<f197>': "\u001b[38;5;197m",
    '<f198>': "\u001b[38;5;198m",
    '<f199>': "\u001b[38;5;199m",
    '<f200>': "\u001b[38;5;200m",
    '<f201>': "\u001b[38;5;201m",
    '<f202>': "\u001b[38;5;202m",
    '<f203>': "\u001b[38;5;203m",
    '<f204>': "\u001b[38;5;204m",
    '<f205>': "\u001b[38;5;205m",
    '<f206>': "\u001b[38;5;206m",
    '<f207>': "\u001b[38;5;207m",
    '<f208>': "\u001b[38;5;208m",
    '<f209>': "\u001b[38;5;209m",
    '<f210>': "\u001b[38;5;210m",
    '<f211>': "\u001b[38;5;211m",
    '<f212>': "\u001b[38;5;212m",
    '<f213>': "\u001b[38;5;213m",
    '<f214>': "\u001b[38;5;214m",
    '<f215>': "\u001b[38;5;215m",
    '<f216>': "\u001b[38;5;216m",
    '<f217>': "\u001b[38;5;217m",
    '<f218>': "\u001b[38;5;218m",
    '<f219>': "\u001b[38;5;219m",
    '<f220>': "\u001b[38;5;220m",
    '<f221>': "\u001b[38;5;221m",
    '<f222>': "\u001b[38;5;222m",
    '<f223>': "\u001b[38;5;223m",
    '<f224>': "\u001b[38;5;224m",
    '<f225>': "\u001b[38;5;225m",
    '<f226>': "\u001b[38;5;226m",
    '<f227>': "\u001b[38;5;227m",
    '<f228>': "\u001b[38;5;228m",
    '<f229>': "\u001b[38;5;229m",
    '<f230>': "\u001b[38;5;230m",
    '<f231>': "\u001b[38;5;231m",
    '<f232>': "\u001b[38;5;232m",
    '<f233>': "\u001b[38;5;233m",
    '<f234>': "\u001b[38;5;234m",
    '<f235>': "\u001b[38;5;235m",
    '<f236>': "\u001b[38;5;236m",
    '<f237>': "\u001b[38;5;237m",
    '<f238>': "\u001b[38;5;238m",
    '<f239>': "\u001b[38;5;239m",
    '<f240>': "\u001b[38;5;240m",
    '<f241>': "\u001b[38;5;241m",
    '<f242>': "\u001b[38;5;242m",
    '<f243>': "\u001b[38;5;243m",
    '<f244>': "\u001b[38;5;244m",
    '<f245>': "\u001b[38;5;245m",
    '<f246>': "\u001b[38;5;246m",
    '<f247>': "\u001b[38;5;247m",
    '<f248>': "\u001b[38;5;248m",
    '<f249>': "\u001b[38;5;249m",
    '<f250>': "\u001b[38;5;250m",
    '<f251>': "\u001b[38;5;251m",
    '<f252>': "\u001b[38;5;252m",
    '<f253>': "\u001b[38;5;253m",
    '<f254>': "\u001b[38;5;254m",
    '<f255>': "\u001b[38;5;255m",
    '<b0>': "\u001b[48;5;0m",
    '<b1>': "\u001b[48;5;1m",
    '<b2>': "\u001b[48;5;2m",
    '<b3>': "\u001b[48;5;3m",
    '<b4>': "\u001b[48;5;4m",
    '<b5>': "\u001b[48;5;5m",
    '<b6>': "\u001b[48;5;6m",
    '<b7>': "\u001b[48;5;7m",
    '<b8>': "\u001b[48;5;8m",
    '<b9>': "\u001b[48;5;9m",
    '<b10>': "\u001b[48;5;10m",
    '<b11>': "\u001b[48;5;11m",
    '<b12>': "\u001b[48;5;12m",
    '<b13>': "\u001b[48;5;13m",
    '<b14>': "\u001b[48;5;14m",
    '<b15>': "\u001b[48;5;15m",
    '<b16>': "\u001b[48;5;16m",
    '<b17>': "\u001b[48;5;17m",
    '<b18>': "\u001b[48;5;18m",
    '<b19>': "\u001b[48;5;19m",
    '<b20>': "\u001b[48;5;20m",
    '<b21>': "\u001b[48;5;21m",
    '<b22>': "\u001b[48;5;22m",
    '<b23>': "\u001b[48;5;23m",
    '<b24>': "\u001b[48;5;24m",
    '<b25>': "\u001b[48;5;25m",
    '<b26>': "\u001b[48;5;26m",
    '<b27>': "\u001b[48;5;27m",
    '<b28>': "\u001b[48;5;28m",
    '<b29>': "\u001b[48;5;29m",
    '<b30>': "\u001b[48;5;30m",
    '<b31>': "\u001b[48;5;31m",
    '<b32>': "\u001b[48;5;32m",
    '<b33>': "\u001b[48;5;33m",
    '<b34>': "\u001b[48;5;34m",
    '<b35>': "\u001b[48;5;35m",
    '<b36>': "\u001b[48;5;36m",
    '<b37>': "\u001b[48;5;37m",
    '<b38>': "\u001b[48;5;38m",
    '<b39>': "\u001b[48;5;39m",
    '<b40>': "\u001b[48;5;40m",
    '<b41>': "\u001b[48;5;41m",
    '<b42>': "\u001b[48;5;42m",
    '<b43>': "\u001b[48;5;43m",
    '<b44>': "\u001b[48;5;44m",
    '<b45>': "\u001b[48;5;45m",
    '<b46>': "\u001b[48;5;46m",
    '<b47>': "\u001b[48;5;47m",
    '<b48>': "\u001b[48;5;48m",
    '<b49>': "\u001b[48;5;49m",
    '<b50>': "\u001b[48;5;50m",
    '<b51>': "\u001b[48;5;51m",
    '<b52>': "\u001b[48;5;52m",
    '<b53>': "\u001b[48;5;53m",
    '<b54>': "\u001b[48;5;54m",
    '<b55>': "\u001b[48;5;55m",
    '<b56>': "\u001b[48;5;56m",
    '<b57>': "\u001b[48;5;57m",
    '<b58>': "\u001b[48;5;58m",
    '<b59>': "\u001b[48;5;59m",
    '<b60>': "\u001b[48;5;60m",
    '<b61>': "\u001b[48;5;61m",
    '<b62>': "\u001b[48;5;62m",
    '<b63>': "\u001b[48;5;63m",
    '<b64>': "\u001b[48;5;64m",
    '<b65>': "\u001b[48;5;65m",
    '<b66>': "\u001b[48;5;66m",
    '<b67>': "\u001b[48;5;67m",
    '<b68>': "\u001b[48;5;68m",
    '<b69>': "\u001b[48;5;69m",
    '<b70>': "\u001b[48;5;70m",
    '<b71>': "\u001b[48;5;71m",
    '<b72>': "\u001b[48;5;72m",
    '<b73>': "\u001b[48;5;73m",
    '<b74>': "\u001b[48;5;74m",
    '<b75>': "\u001b[48;5;75m",
    '<b76>': "\u001b[48;5;76m",
    '<b77>': "\u001b[48;5;77m",
    '<b78>': "\u001b[48;5;78m",
    '<b79>': "\u001b[48;5;79m",
    '<b80>': "\u001b[48;5;80m",
    '<b81>': "\u001b[48;5;81m",
    '<b82>': "\u001b[48;5;82m",
    '<b83>': "\u001b[48;5;83m",
    '<b84>': "\u001b[48;5;84m",
    '<b85>': "\u001b[48;5;85m",
    '<b86>': "\u001b[48;5;86m",
    '<b87>': "\u001b[48;5;87m",
    '<b88>': "\u001b[48;5;88m",
    '<b89>': "\u001b[48;5;89m",
    '<b90>': "\u001b[48;5;90m",
    '<b91>': "\u001b[48;5;91m",
    '<b92>': "\u001b[48;5;92m",
    '<b93>': "\u001b[48;5;93m",
    '<b94>': "\u001b[48;5;94m",
    '<b95>': "\u001b[48;5;95m",
    '<b96>': "\u001b[48;5;96m",
    '<b97>': "\u001b[48;5;97m",
    '<b98>': "\u001b[48;5;98m",
    '<b99>': "\u001b[48;5;99m",
    '<b100>': "\u001b[48;5;100m",
    '<b101>': "\u001b[48;5;101m",
    '<b102>': "\u001b[48;5;102m",
    '<b103>': "\u001b[48;5;103m",
    '<b104>': "\u001b[48;5;104m",
    '<b105>': "\u001b[48;5;105m",
    '<b106>': "\u001b[48;5;106m",
    '<b107>': "\u001b[48;5;107m",
    '<b108>': "\u001b[48;5;108m",
    '<b109>': "\u001b[48;5;109m",
    '<b110>': "\u001b[48;5;110m",
    '<b111>': "\u001b[48;5;111m",
    '<b112>': "\u001b[48;5;112m",
    '<b113>': "\u001b[48;5;113m",
    '<b114>': "\u001b[48;5;114m",
    '<b115>': "\u001b[48;5;115m",
    '<b116>': "\u001b[48;5;116m",
    '<b117>': "\u001b[48;5;117m",
    '<b118>': "\u001b[48;5;118m",
    '<b119>': "\u001b[48;5;119m",
    '<b120>': "\u001b[48;5;120m",
    '<b121>': "\u001b[48;5;121m",
    '<b122>': "\u001b[48;5;122m",
    '<b123>': "\u001b[48;5;123m",
    '<b124>': "\u001b[48;5;124m",
    '<b125>': "\u001b[48;5;125m",
    '<b126>': "\u001b[48;5;126m",
    '<b127>': "\u001b[48;5;127m",
    '<b128>': "\u001b[48;5;128m",
    '<b129>': "\u001b[48;5;129m",
    '<b130>': "\u001b[48;5;130m",
    '<b131>': "\u001b[48;5;131m",
    '<b132>': "\u001b[48;5;132m",
    '<b133>': "\u001b[48;5;133m",
    '<b134>': "\u001b[48;5;134m",
    '<b135>': "\u001b[48;5;135m",
    '<b136>': "\u001b[48;5;136m",
    '<b137>': "\u001b[48;5;137m",
    '<b138>': "\u001b[48;5;138m",
    '<b139>': "\u001b[48;5;139m",
    '<b140>': "\u001b[48;5;140m",
    '<b141>': "\u001b[48;5;141m",
    '<b142>': "\u001b[48;5;142m",
    '<b143>': "\u001b[48;5;143m",
    '<b144>': "\u001b[48;5;144m",
    '<b145>': "\u001b[48;5;145m",
    '<b146>': "\u001b[48;5;146m",
    '<b147>': "\u001b[48;5;147m",
    '<b148>': "\u001b[48;5;148m",
    '<b149>': "\u001b[48;5;149m",
    '<b150>': "\u001b[48;5;150m",
    '<b151>': "\u001b[48;5;151m",
    '<b152>': "\u001b[48;5;152m",
    '<b153>': "\u001b[48;5;153m",
    '<b154>': "\u001b[48;5;154m",
    '<b155>': "\u001b[48;5;155m",
    '<b156>': "\u001b[48;5;156m",
    '<b157>': "\u001b[48;5;157m",
    '<b158>': "\u001b[48;5;158m",
    '<b159>': "\u001b[48;5;159m",
    '<b160>': "\u001b[48;5;160m",
    '<b161>': "\u001b[48;5;161m",
    '<b162>': "\u001b[48;5;162m",
    '<b163>': "\u001b[48;5;163m",
    '<b164>': "\u001b[48;5;164m",
    '<b165>': "\u001b[48;5;165m",
    '<b166>': "\u001b[48;5;166m",
    '<b167>': "\u001b[48;5;167m",
    '<b168>': "\u001b[48;5;168m",
    '<b169>': "\u001b[48;5;169m",
    '<b170>': "\u001b[48;5;170m",
    '<b171>': "\u001b[48;5;171m",
    '<b172>': "\u001b[48;5;172m",
    '<b173>': "\u001b[48;5;173m",
    '<b174>': "\u001b[48;5;174m",
    '<b175>': "\u001b[48;5;175m",
    '<b176>': "\u001b[48;5;176m",
    '<b177>': "\u001b[48;5;177m",
    '<b178>': "\u001b[48;5;178m",
    '<b179>': "\u001b[48;5;179m",
    '<b180>': "\u001b[48;5;180m",
    '<b181>': "\u001b[48;5;181m",
    '<b182>': "\u001b[48;5;182m",
    '<b183>': "\u001b[48;5;183m",
    '<b184>': "\u001b[48;5;184m",
    '<b185>': "\u001b[48;5;185m",
    '<b186>': "\u001b[48;5;186m",
    '<b187>': "\u001b[48;5;187m",
    '<b188>': "\u001b[48;5;188m",
    '<b189>': "\u001b[48;5;189m",
    '<b190>': "\u001b[48;5;190m",
    '<b191>': "\u001b[48;5;191m",
    '<b192>': "\u001b[48;5;192m",
    '<b193>': "\u001b[48;5;193m",
    '<b194>': "\u001b[48;5;194m",
    '<b195>': "\u001b[48;5;195m",
    '<b196>': "\u001b[48;5;196m",
    '<b197>': "\u001b[48;5;197m",
    '<b198>': "\u001b[48;5;198m",
    '<b199>': "\u001b[48;5;199m",
    '<b200>': "\u001b[48;5;200m",
    '<b201>': "\u001b[48;5;201m",
    '<b202>': "\u001b[48;5;202m",
    '<b203>': "\u001b[48;5;203m",
    '<b204>': "\u001b[48;5;204m",
    '<b205>': "\u001b[48;5;205m",
    '<b206>': "\u001b[48;5;206m",
    '<b207>': "\u001b[48;5;207m",
    '<b208>': "\u001b[48;5;208m",
    '<b209>': "\u001b[48;5;209m",
    '<b210>': "\u001b[48;5;210m",
    '<b211>': "\u001b[48;5;211m",
    '<b212>': "\u001b[48;5;212m",
    '<b213>': "\u001b[48;5;213m",
    '<b214>': "\u001b[48;5;214m",
    '<b215>': "\u001b[48;5;215m",
    '<b216>': "\u001b[48;5;216m",
    '<b217>': "\u001b[48;5;217m",
    '<b218>': "\u001b[48;5;218m",
    '<b219>': "\u001b[48;5;219m",
    '<b220>': "\u001b[48;5;220m",
    '<b221>': "\u001b[48;5;221m",
    '<b222>': "\u001b[48;5;222m",
    '<b223>': "\u001b[48;5;223m",
    '<b224>': "\u001b[48;5;224m",
    '<b225>': "\u001b[48;5;225m",
    '<b226>': "\u001b[48;5;226m",
    '<b227>': "\u001b[48;5;227m",
    '<b228>': "\u001b[48;5;228m",
    '<b229>': "\u001b[48;5;229m",
    '<b230>': "\u001b[48;5;230m",
    '<b231>': "\u001b[48;5;231m",
    '<b232>': "\u001b[48;5;232m",
    '<b233>': "\u001b[48;5;233m",
    '<b234>': "\u001b[48;5;234m",
    '<b235>': "\u001b[48;5;235m",
    '<b236>': "\u001b[48;5;236m",
    '<b237>': "\u001b[48;5;237m",
    '<b238>': "\u001b[48;5;238m",
    '<b239>': "\u001b[48;5;239m",
    '<b240>': "\u001b[48;5;240m",
    '<b241>': "\u001b[48;5;241m",
    '<b242>': "\u001b[48;5;242m",
    '<b243>': "\u001b[48;5;243m",
    '<b244>': "\u001b[48;5;244m",
    '<b245>': "\u001b[48;5;245m",
    '<b246>': "\u001b[48;5;246m",
    '<b247>': "\u001b[48;5;247m",
    '<b248>': "\u001b[48;5;248m",
    '<b249>': "\u001b[48;5;249m",
    '<b250>': "\u001b[48;5;250m",
    '<b251>': "\u001b[48;5;251m",
    '<b252>': "\u001b[48;5;252m",
    '<b253>': "\u001b[48;5;253m",
    '<b254>': "\u001b[48;5;254m",
    '<b255>': "\u001b[48;5;255m",
    '<u>': "\u001b[4m",
    '<b>': "\u001b[1m",
    '<r>': "\u001b[0m"
}

# Create a regular expression from the dictionary keys
pattern = re.compile("(%s)" % "|".join(map(re.escape, dict.keys())))


def cmsg(text):
    # For each match, look-up corresponding value in dictionary
    return pattern.sub(
        lambda mo: dict[mo.string[mo.start(): mo.end()]], text) + "\u001b[0m"
