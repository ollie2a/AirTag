import argparse
import time
import os
import curses
from subprocess import check_call as shell_cmd
from datetime import datetime
from tabulate import tabulate
from functools import partial
from lib.constants import JSON_LAYER_SEPARATOR
from lib.constants import FINDMY_FILES
from lib.constants import NAME_SEPARATOR
from lib.constants import JSON_LAYER_SEPARATOR
from lib.constants import NULL_STR
from lib.constants import TIME_FORMAT
from lib.constants import DATE_FORMAT
from lib.log_manager import LogManager

# 	serialnumber=$(jq ".[$j].serialNumber" "$ITEMS_FILE")
# 	name=$(jq ".[$j].name" "$ITEMS_FILE")
# 	producttype=$(jq ".[$j].productType.type" "$ITEMS_FILE")
# 	productindentifier=$(jq ".[$j].productType.productInformation.productIdentifier" "$ITEMS_FILE")
# 	vendoridentifier=$(jq ".[$j].productType.productInformation.vendorIdentifier" "$ITEMS_FILE")
# 	antennapower=$(jq ".[$j].productType.productInformation.antennaPower" "$ITEMS_FILE")
# 	systemversion=$(jq ".[$j].systemVersion" "$ITEMS_FILE")
# 	batterystatus=$(jq ".[$j].batteryStatus" "$ITEMS_FILE")
# 	locationpositiontype=$(jq ".[$j].location.positionType" "$ITEMS_FILE")
# 	locationlatitude=$(jq ".[$j].location.latitude" "$ITEMS_FILE")
# 	locationlongitude=$(jq ".[$j].location.longitude" "$ITEMS_FILE")
# 	locationtimestamp=$(jq ".[$j].location.timeStamp" "$ITEMS_FILE")
# 	locationverticalaccuracy=$(jq ".[$j].location.verticalAccuracy // 0" "$ITEMS_FILE")
# 	locationhorizontalaccuracy=$(jq ".[$j].location.horizontalAccuracy // 0" "$ITEMS_FILE")
# 	locationfloorlevel=$(jq ".[$j].location.floorlevel // 0" "$ITEMS_FILE")
# 	locationaltitude=$(jq ".[$j].location.altitude // 0" "$ITEMS_FILE")
# 	locationisinaccurate=$(jq ".[$j].location.isInaccurate" "$ITEMS_FILE" | awk '{ print "\""$0"\"" }')
# 	locationisold=$(jq ".[$j].location.isOld" "$ITEMS_FILE" | awk '{ print "\""$0"\"" }' )
# 	locationfinished=$(jq ".[$j].location.locationFinished" "$ITEMS_FILE" | awk '{ print "\""$0"\"" }' )
# 	addresslabel=$(jq ".[$j].address.label // \"\"" "$ITEMS_FILE")
# 	addressstreetaddress=$(jq ".[$j].address.streetAddress // \"\"" "$ITEMS_FILE")
# 	addresscountrycode=$(jq ".[$j].address.countryCode // \"\"" "$ITEMS_FILE")
# 	addressstatecode=$(jq ".[$j].address.stateCode // \"\"" "$ITEMS_FILE")
# 	addressadministrativearea=$(jq ".[$j].address.administrativeArea // \"\"" "$ITEMS_FILE")
# 	addressstreetname=$(jq ".[$j].address.streetName // \"\"" "$ITEMS_FILE")
# 	addresslocality=$(jq ".[$j].address.locality // \"\"" "$ITEMS_FILE")
# 	addresscountry=$(jq ".[$j].address.country // \"\"" "$ITEMS_FILE")
# 	addressareaofinteresta=$(jq ".[$j].address.areaOfInterest[0] // \"\"" "$ITEMS_FILE")
# 	addressareaofinterestb=$(jq ".[$j].address.areaOfInterest[1] // \"\"" "$ITEMS_FILE")

def parse_args():
    parser = argparse.ArgumentParser(
        description='Record Apple findmy history for Apple devices.')
    parser.add_argument(
        '--refresh',
        type=int,
        action='store',
        default=100,
        help='Refresh interval (ms).')
    parser.add_argument(
        '--name_keys',
        type=str,
        action='append',
        default=['name', 'deviceDiscoveryId', 'serialNumber'],
        help='Keys used to construct the filename for each device.')
    parser.add_argument(
        '--store_keys',
        type=str,
        action='append',
        default=['name', 'batteryLevel', 'batteryStatus', 'batteryLevel',
                 f'location{JSON_LAYER_SEPARATOR}timeStamp',
                 f'location{JSON_LAYER_SEPARATOR}latitude',
                 f'location{JSON_LAYER_SEPARATOR}longitude',
                 f'location{JSON_LAYER_SEPARATOR}verticalAccuracy',
                 f'location{JSON_LAYER_SEPARATOR}horizontalAccuracy',
                 f'location{JSON_LAYER_SEPARATOR}altitude',
                 f'location{JSON_LAYER_SEPARATOR}positionType',
                 f'location{JSON_LAYER_SEPARATOR}floorLevel',
                 f'location{JSON_LAYER_SEPARATOR}isInaccurate',
                 f'location{JSON_LAYER_SEPARATOR}isOld',
                 f'location{JSON_LAYER_SEPARATOR}locationFinished',
                 f'address{JSON_LAYER_SEPARATOR}label',
                 f'address{JSON_LAYER_SEPARATOR}streetAddress',
                 f'address{JSON_LAYER_SEPARATOR}countryCode',
                 f'address{JSON_LAYER_SEPARATOR}stateCode',
                 f'address{JSON_LAYER_SEPARATOR}administrativeArea',
                 f'address{JSON_LAYER_SEPARATOR}streetName',
                 f'address{JSON_LAYER_SEPARATOR}locality',
                 f'address{JSON_LAYER_SEPARATOR}country',
                 'id', 'deviceDiscoveryId', 'baUUID', 'serialNumber',
                 'identifier', 'prsId',
                 'deviceModel', 'modelDisplayName', 'deviceDisplayName'],
        help='Keys to log.')
    parser.add_argument(
        '--timestamp_key',
        type=str,
        action='store',
        default=f'location{JSON_LAYER_SEPARATOR}timeStamp',
        help='The key of timestamp in findmy JSON')
    parser.add_argument(
        '--log_folder',
        type=str,
        action='store',
        default='log',
        help='The path of log folder.')
    parser.add_argument(
        '--no_date_folder',
        action='store_true',
        help='By default, the logs of each day will be saved in a separated '
             'folder. Use this option to turn it off.')
    args = parser.parse_args()

    return args


def main(stdscr, args):
    stdscr.clear()
    args = parse_args()
    log_manager = LogManager(
        findmy_files=[os.path.expanduser(f) for f in FINDMY_FILES],
        store_keys=args.store_keys,
        timestamp_key=args.timestamp_key,
        log_folder=args.log_folder,
        name_keys=args.name_keys,
        name_separator=NAME_SEPARATOR,
        json_layer_separator=JSON_LAYER_SEPARATOR,
        null_str=NULL_STR,
        date_format=DATE_FORMAT,
        no_date_folder=args.no_date_folder)
    while True:
        log_manager.refresh_log()
        latest_log, log_cnt = log_manager.get_latest_log()
        table = []
        for name, log in latest_log.items():
            latest_time = log[args.timestamp_key]
            if isinstance(latest_time, int) or isinstance(latest_time, float):
                latest_time = datetime.fromtimestamp(
                    float(latest_time) / 1000.)
                latest_time = latest_time.strftime(TIME_FORMAT)
            table.append([name, latest_time, log_cnt[name]])
        table = tabulate(
            table,
            headers=['Name', 'Last update', 'Log count'],
            tablefmt="github")

        stdscr.erase()
        try:
            stdscr.addstr(
                0, 0, f'Current time: {datetime.now().strftime(TIME_FORMAT)}')
            stdscr.addstr(1, 0, table)
        except:
            pass
        stdscr.refresh()

        time.sleep(float(args.refresh) / 1000)


if __name__ == "__main__":
    try:
        shell_cmd("open -gja /System/Applications/FindMy.app", shell=True)
    except:
        # Maybe Apple changed the name or the dir of the app?
        pass
    args = parse_args()
    curses.wrapper(partial(main, args=args))
