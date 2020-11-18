import bs4
import csv
import sys
import os
import argparse

def parse_arguments():

    parser = argparse.ArgumentParser(description='Convert netxml files to csv files')
    parser.add_argument('input', help='List of *.netxml files to process separated by commas')
    parser.add_argument('-p', '--prefix', default='output_', help='Output filename prefix.  (Default output_)')

    args = parser.parse_args()

    return args

def main(args):
    input_file_list = args.input.split(",")
    prefix = args.prefix

    network_list = []
    client_list = []

    for input_file in input_file_list:

        # Verify file exists
        if not os.path.exists(input_file):
            print("[!] {} does not exist, skipping...".format(input_file))
            continue

        # Verify the file extension is *.netxml
        _, file_extension = os.path.splitext(input_file)

        if file_extension != '.netxml':
            print("[!] {} is not a *.netxml file.  skipping...".format(input_file))
            continue

        print("[*] Begin processing {}".format(input_file))

        with open(input_file, 'r') as f:

            contents = f.read()

            soup = bs4.BeautifulSoup(contents, 'lxml')

            wifi_networks = soup.find_all('wireless-network')

            for network in wifi_networks:

                wireless_clients = network.find_all('wireless-client')

                bssid = ''
                encryption = ''
                essid = ''
                cloaked = ''
                manuf = ''
                channel = ''
                freqmhz = ''
                carrier = ''
                last_signal_rssi = ''
                latitude = ''
                longitude = ''
                first_seen = ''
                last_seen = ''
                encryption = []
                
                network_type = network['type']

                for child in network.children:

                    if isinstance(child, bs4.element.Tag):

                        if child.name == 'ssid':
                            first_seen = child.attrs['first-time']
                            last_seen = child.attrs['last-time']

                            for s in child.children:
                                if s.name == 'encryption':
                                    encryption.append(s.string)

                                if s.name == 'essid':
                                    essid = s.string
                                    cloaked = s.attrs['cloaked']

                        elif child.name == 'bssid':
                            bssid = child.string

                        elif child.name == 'manuf':
                            manuf = child.string

                        elif child.name == 'channel':
                            channel = child.string

                        elif child.name == 'freqmhz':
                            freqmhz = child.string
                        
                        elif child.name == 'carrier':
                            carrier = child.string

                        elif child.name == 'snr-info':
                            for s in child.children:
                                if s.name == 'last_signal_rssi':
                                    last_signal_rssi = s.string
                                    break

                        elif child.name == 'gps-info':
                            for s in child.children:
                                if s.name == 'avg-lat':
                                    latitude = s.string

                                if s.name == 'avg-lon':
                                    longitude = s.string

                network_dict = dict()

                network_dict = {
                    'network-type':network_type,
                    'essid': essid,
                    'cloaked': cloaked,
                    'bssid': bssid,
                    'manuf': manuf,
                    'channel': channel,
                    'lat': latitude,
                    'long': longitude,
                    'encryption': ','.join(encryption),
                    'freqmhz': freqmhz,
                    'carrier': carrier,
                    'rssi': last_signal_rssi 
                }

                network_list.append(network_dict)

                # get information for wireless-clients
                if len(wireless_clients) > 0:

                    for client in wireless_clients:                

                        first_seen = client['first-time']
                        last_seen = client['last-time']
                        network_type = client['type']

                        client_mac = ''
                        client_manuf = ''

                        for child in client.children:

                            if child.name == 'client-mac':
                                client_mac = child.string

                            elif child.name == 'client-manuf':
                                client_manuf = child.string

                            elif child.name == 'channel':
                                channel = child.string

                            elif child.name == 'snr-info':
                                for s in child.children:
                                    if s.name == 'last_signal_rssi':
                                        last_signal_rssi = s.string
                                        break

                            elif child.name == 'gps-info':
                                for s in child.children:
                                    if s.name == 'avg-lat':
                                        latitude = s.string

                                    if s.name == 'avg-lon':
                                        longitude = s.string

                            ssid_list = client.find_all('ssid')
                            ssid_set = set()

                            if len(ssid_list) > 0:

                                for ssid in ssid_list:
                                    for child in ssid.children:
                                        if child.name == 'ssid':
                                            ssid_set.add(child.string)

                        client_dict = dict()
                        client_dict = {
                            'client_mac': client_mac,
                            'client_manuf': client_manuf,
                            'first_seen': first_seen,
                            'last_seen': last_seen,
                            'probed_essids': ','.join(ssid_set),
                            'network_type': network_type,
                            'rssi': last_signal_rssi,
                            'latitude': latitude,
                            'longitude': longitude,
                            'connected_essid': essid,
                            'connected_bssid': bssid,
                            'channel': channel
                        }

                        client_list.append(client_dict)

    # Show some metrics
    num = len([token['bssid'] for token in network_list if token['network-type'] == 'infrastructure'])
    print("Number of BSSIDs Collected: {}".format(len(network_list)))

    num = len(set([token['essid'] for token in network_list ]))
    print("Number of Unique ESSIDs: {}".format(num))

    num = len([token['essid'] for token in network_list if token['cloaked'] == 'true'])
    print("Number of Hidden ESSIDss: {}".format(num))

    print("Number of Clients Collected: {}".format(len(client_list)))

    # Write the results to csv files
    if network_list:

        outfilename = prefix + '.wireless-network.csv'

        with open(outfilename, 'w', newline='', encoding='utf-8') as csvfile:

            fieldnames = ['network-type', 'essid', 'cloaked', 'bssid', 'manuf', 'channel', 'lat', 'long', 'encryption', 'freqmhz', 'carrier', 'rssi']

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(network_list)

        print("[*] Wrote wirless-network information to {}".format(outfilename))

    if client_list:

        outfilename = prefix + '.wireless-clients.csv'
        with open(outfilename, 'w', newline='', encoding='utf-8') as csvfile:

            fieldnames = ['client_mac','client_manuf','first_seen','last_seen','probed_essids','network_type','rssi','latitude','longitude','connected_essid','connected_bssid', 'channel']

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(client_list)

        print("[*] Wrote wireless-client information to {}".format(outfilename))

if __name__ == '__main__':
    args = parse_arguments()
    main(args)