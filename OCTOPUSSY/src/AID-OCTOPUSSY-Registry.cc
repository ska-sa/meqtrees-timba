    // This file is generated automatically -- do not edit
    // Generated by /home/oms/LOFAR/autoconf_share/../TIMBA/DMI/aid/build_aid_maps.pl
    #include <DMI/AtomicID.h>
    #include <DMI/TypeInfo.h>
    #include <DMI/DynamicTypeManager.h>
    #include <DMI/Packer.h>
#include "Message.h"
DMI::BObj * __construct_OctopussyMessage (int n) { return n>0 ? new Octopussy::Message [n] : new Octopussy::Message; }
    using namespace DMI;
  
    int aidRegistry_OCTOPUSSY ()
    {
      static int res = 

        AtomicID::registerId(-1471,"loggerwp")+
        AtomicID::registerId(-1461,"max")+
        AtomicID::registerId(-1426,"level")+
        AtomicID::registerId(-1331,"scope")+
        AtomicID::registerId(-1454,"reflectorwp")+
        AtomicID::registerId(-1449,"reflect")+
        AtomicID::registerId(-1437,"octopussymessage")+
        TypeInfoReg::addToRegistry(-1437,TypeInfo(TypeInfo::DYNAMIC,0))+
        DynamicTypeManager::addToRegistry(-1437,__construct_OctopussyMessage)+
        AtomicID::registerId(-1055,"index")+
        AtomicID::registerId(-1339,"text")+
        AtomicID::registerId(-1452,"dispatcher")+
        AtomicID::registerId(-1366,"local")+
        AtomicID::registerId(-1406,"publish")+
        AtomicID::registerId(-1442,"argv")+
        AtomicID::registerId(-1466,"subscriptions")+
        AtomicID::registerId(-1085,"init")+
        AtomicID::registerId(-1446,"heartbeat")+
        AtomicID::registerId(-1472,"connectionmgrwp")+
        AtomicID::registerId(-1451,"gwserverwp")+
        AtomicID::registerId(-1429,"gwclientwp")+
        AtomicID::registerId(-1464,"gatewaywp")+
        AtomicID::registerId(-1450,"timestamp")+
        AtomicID::registerId(-1430,"gw")+
        AtomicID::registerId(-1467,"client")+
        AtomicID::registerId(-1458,"server")+
        AtomicID::registerId(-1444,"bind")+
        AtomicID::registerId(-1350,"error")+
        AtomicID::registerId(-1474,"fatal")+
        AtomicID::registerId(-1468,"bound")+
        AtomicID::registerId(-1448,"remote")+
        AtomicID::registerId(-1427,"up")+
        AtomicID::registerId(-1470,"down")+
        AtomicID::registerId(-1440,"network")+
        AtomicID::registerId(-1287,"type")+
        AtomicID::registerId(-1455,"duplicate")+
        AtomicID::registerId(-1340,"host")+
        AtomicID::registerId(-1435,"port")+
        AtomicID::registerId(-1433,"peers")+
        AtomicID::registerId(-1436,"connected")+
        AtomicID::registerId(-1441,"connection")+
        AtomicID::registerId(-1065,"add")+
        AtomicID::registerId(-1431,"open")+
        AtomicID::registerId(-1445,"msglog")+
        AtomicID::registerId(-1463,"lognormal")+
        AtomicID::registerId(-1456,"logwarning")+
        AtomicID::registerId(-1432,"logerror")+
        AtomicID::registerId(-1457,"logfatal")+
        AtomicID::registerId(-1462,"logdebug")+
        AtomicID::registerId(-1434,"wp")+
        AtomicID::registerId(-1349,"event")+
        AtomicID::registerId(-1469,"timeout")+
        AtomicID::registerId(-1354,"input")+
        AtomicID::registerId(-1438,"signal")+
        AtomicID::registerId(-1428,"subscribe")+
        AtomicID::registerId(-1473,"hello")+
        AtomicID::registerId(-1439,"bye")+
        AtomicID::registerId(-1059,"state")+
        AtomicID::registerId(-1465,"reconnect")+
        AtomicID::registerId(-1443,"failconnect")+
        AtomicID::registerId(-1447,"reopen")+
        AtomicID::registerId(-1043,"list")+
        AtomicID::registerId(-1460,"hosts")+
        AtomicID::registerId(-1453,"ports")+
        AtomicID::registerId(-1459,"gateway")+
    0;
    return res;
  }
  
  int __dum_call_registries_for_OCTOPUSSY = aidRegistry_OCTOPUSSY();

