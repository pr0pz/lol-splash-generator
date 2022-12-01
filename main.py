"""
LoL Intro Splash HTML file (e.g. for Stream)

v1.1
"""
import time
import requests  # for curl request
import re  # For regex
from colorama import just_fix_windows_console, Fore, Back, Style  # for cool looking colors - https://pypi.org/project/colorama/

# Disable request warnings
requests.packages.urllib3.disable_warnings()

"""
Change these vars to match your settings
"""
HTML_FILE = 'template.html'  # File that will be generated inside the folder of this script
SUMMONER_NAME = 'pr0pz'  # If you change accounts, you must change the nick in here
INTERVAL = 1  # Client check interval
INTERVAL_LONG = 180

"""
Data Dragon Documentation: https://developer.riotgames.com/docs/lol#data-dragon
"""
API_URL = 'https://127.0.0.1:2999/liveclientdata/allgamedata'
LOL_VERSION = '12.22.1'
CDN_URL = 'https://ddragon.leagueoflegends.com/cdn/' + LOL_VERSION
# Champ info: https://cdn.communitydragon.org/{LOL_VERSION}/champion/{championName}
# https://ddragon.leagueoflegends.com/cdn/12.22.1/data/en_US/champion/Nautilus.json
CDN_URL_CHAMPION = CDN_URL + '/data/en_US/champion/'
# Champ image: http://ddragon.leagueoflegends.com/cdn/img/champion/splash/{championName}_{skinNum}.jpg
# http://ddragon.leagueoflegends.com/cdn/img/champion/splash/Nautilus_0.jpg
CDN_URL_CHAMPION_IMAGE = 'https://ddragon.leagueoflegends.com/cdn/img/champion/splash/'
IMAGE_FOLDER = 'img/'
STATUS_MESSAGE = ''

# Start function
def start():

    global LOL_VERSION

    # Needed for correct colors in console
    just_fix_windows_console()

    # Get current lol version
    try:
        response = requests.get( 'https://ddragon.leagueoflegends.com/api/versions.json' )

        if response.ok and response.json():
            request_data = response.json()

            # Save if version differs
            if LOL_VERSION != request_data[0]:
                LOL_VERSION = request_data[0]
                log( Fore.GREEN + 'Updated LoL version: ' + Style.RESET_ALL + LOL_VERSION )

            else:
                log( Fore.GREEN + 'Current LoL version: ' + Style.RESET_ALL + LOL_VERSION )

    except requests.exceptions.RequestException as e:
        log( Fore.YELLOW + 'Couldn\'t fetch new version: ' + Style.RESET_ALL + 'Using version ' + LOL_VERSION )

    # Run the Script
    update_live_client_data()


# Fetch live client data
def update_live_client_data() :

    global INTERVAL, INTERVAL_LONG

    try:
        response = requests.get( API_URL, verify=False )
        # Check if we get something
        if response.ok and response.json():
            debug( response.json() )
            log( Fore.GREEN + 'Status: ' + Style.RESET_ALL + str( response.status_code ) + ' / ' + response.reason )

            if response.status_code != 404 and INTERVAL != INTERVAL_LONG:
                player_data = get_player_data( response.json() )
                player_data = get_champion_id( player_data )
                player_data = get_proper_skinid( player_data )
                player_data = save_splash_image( player_data )
                update_html( player_data )
                # Send sound signal when ready
                print( '\007\007' )

                # Game has already started, so we don't need to check every second.
                # It will change back to one second before another game start.
                INTERVAL = INTERVAL_LONG

        else:
            # No game running, so set interval to 1 second.
            log( Fore.YELLOW + 'Client not running: ' + Style.RESET_ALL + str( response.status_code ) )
            INTERVAL = 1

    except Exception as e:
        # No game running, so set interval to 1 second.
        INTERVAL = 1
        seconds = ' second.' if INTERVAL == 1 else ' seconds.'
        log( Fore.YELLOW + 'Client not running.' + Style.RESET_ALL + ' Recheck runs every ' + str( INTERVAL ) + seconds )

    # Just runs every X seconds forever :)
    while True:
        time.sleep( INTERVAL )
        update_live_client_data()


# Get basic player data
def get_player_data( game_data ):

    global SUMMONER_NAME

    player_data = {
        'champion_name': '',
        'champion_id': '',
        'skin_name': '',
        'skin_id': 0,
        'image_filename': '',
        'image_path': ''
    }

    if game_data:

        # Loop all players
        for player in game_data['allPlayers']:

            # Check if it's us
            if 'summonerName' in player and player['summonerName'] == SUMMONER_NAME :

                # Save the name of our current champion
                if 'championName' in player:
                    player_data['champion_name'] = player.get('championName')

                    # We need the exact skin name for getting the right picture to display
                    if 'skinName' in player:
                        player_data['skin_name'] = player.get('skinName')
                        log( Fore.GREEN + 'Found skin name: ' + Style.RESET_ALL + player_data['skin_name'] )

                    # No skinName == Default skin
                    else:
                        log( Fore.GREEN + 'Using default skin: ' + Style.RESET_ALL + 'No skin name found.' )

                else:
                    debug( game_data )
                    log( Fore.RED + 'Champion name not found: ' + Style.RESET_ALL + 'Check data.json for more information.' )
                    exit()

    return player_data


# Get official champion id
def get_champion_id( player_data ):

    url = CDN_URL + '/data/en_US/champion.json'

    # Get all champions
    response = requests.get( url )

    if response.ok and response.json():
        champions = response.json()['data']

        # Loop all champions and look for match
        for champion_name in champions:
            if champions[ champion_name ]['name'] == player_data['champion_name']:
                player_data['champion_id'] = champions[ champion_name ]['id']
                break

    else:
        # No game running, so set interval to 1 second.
        log( Fore.RED + 'Couldn\'t fetch champions.' + Style.RESET_ALL  )
        exit()

    return player_data


# Get the right skin id (wrong chroma id, no image)
def get_proper_skinid( player_data ):

    # Set up current champion info url
    champion_url = CDN_URL_CHAMPION + player_data['champion_id'] + '.json'

    # Get champion info
    response = requests.get( champion_url )

    if response.ok and response.json():

        champion_data = response.json()
        log( Fore.GREEN + 'Fetched champion info: ' + Style.RESET_ALL + player_data['champion_name'] )

        # Get detailed champ data
        champion = champion_data['data'][ player_data['champion_id'] ]

        # Loop all skins and check for match
        for skin in champion['skins']:
            if 'name' in skin and player_data['skin_name'] == skin['name']:
                player_data['skin_id'] = skin['num']
                log( Fore.GREEN + 'Found Skin ID: ' + Style.RESET_ALL + str( player_data['skin_id'] ) + ' ( ' + player_data['skin_name'] + ' )' )

    else:
        log( Fore.RED + 'Couldn\'t fetch champion info: ' + Style.RESET_ALL + 'Check data.json for more information.' )

    return player_data


# Save Splash image to local folder
def save_splash_image( player_data ):

    # Local image filename
    player_data['image_filename'] = player_data['champion_id'] + '_' + str( player_data['skin_id'] ) + '.jpg'
    player_data['image_path'] = IMAGE_FOLDER + player_data['image_filename']

    # Remote Image URL
    image_splash_url = CDN_URL_CHAMPION_IMAGE + player_data['image_filename']

    # Check if file exists
    try:
        img_file = open( player_data['image_path'] )
        img_file.close()
        log( Fore.GREEN + 'Image already exists.' + Style.RESET_ALL )

    # No, so download and save
    except Exception as e:

        # Get remote image content
        img = requests.get( image_splash_url ).content
        # Open and write img file locally
        img_file = open( player_data['image_path'], 'wb' )
        img_file.write( img )
        img_file.close()
        log( Fore.GREEN + 'New image saved: ' + Style.RESET_ALL + player_data['image_filename'] )

    return player_data


# Build actual HTML markup
def update_html( player_data ) :

    html_data = ''

    # Get template data
    try:
        template = open( 'template.html', 'r' )
        html_data = template.read()
        template.close()

    except Exception as e:
        log( Fore.RED + 'Template file not found: ' + Style.RESET_ALL + 'Download the template file manually from the github repository.' )
        exit()

    if html_data:
        # Search and replace
        # We have to search first, since we only need the matched group to be replaced.
        search = re.search( r'url\((.*)\)', html_data )
        html_data = re.sub( search.group(1), player_data['image_path'], html_data )
        search = re.search( r'<div id="splash-content">(.*)</div>', html_data )
        html_data = re.sub( search.group(1), player_data['champion_name'], html_data )

        # Write new data to output file
        stream = open( 'template.html', 'w+' )
        stream.write( html_data )
        stream.close()

        log( Fore.GREEN + 'HTML build and saved.' + Style.RESET_ALL )
    
    else:
        log( Fore.RED + 'HTML not saved: ' + Style.RESET_ALL + ' Data is empty.' )


# Print Status messages
def log( s ):
    global STATUS_MESSAGE
    if s != STATUS_MESSAGE:
        print( ' > ' + s )
        STATUS_MESSAGE = s

# Write debug file
def debug( data ):
	# Write json debug file
	file = open( 'data.json', 'w+' )
	file.write( str( data ) )
	file.close()

start()