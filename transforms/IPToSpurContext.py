from extensions import registry
from maltego_trx.maltego import UIM_TYPES, MaltegoMsg, MaltegoTransform, LINK_STYLE_DASHED
from maltego_trx.transform import DiscoverableTransform
from maltego_trx.overlays import OverlayPosition, OverlayType
from settings import language_setting, api_key_setting
from api.spur import get_context_for_ip
import ipaddress



@registry.register_transform(display_name='IPv4 to Spur Context',
                             input_entity='maltego.IPv4Address',
                             description='Spur VPN/ Proxy/ Residential Proxy Context for an IP address.',
                             settings=[language_setting, api_key_setting],
                             output_entities=['maltego.Location', 'maltego.AS', 'maltego.Phrase'])
@registry.register_transform(display_name='IPv6 to Spur Context',
                             input_entity='maltego.IPv6Address',
                             description='Spur VPN/ Proxy/ Residential Proxy Context for an IP address.',
                             settings=[language_setting, api_key_setting],
                             output_entities=['maltego.Location', 'maltego.AS', 'maltego.Phrase'])
class IPToSpurContext(DiscoverableTransform):
    '''
    Transform to get Spur Context for an IP address.
    
    This transform requires an API key from Spur Intelligence.
    The Spur Context API will handle either IPv4 or IPv6 addresses, but
    since Maltego treats them as separate entities, the transform is registered
    twice - once for each entity type.  This simply means that the API key must be
    entered the first time the transform is used for both IPv4 and IPv6 entities.

    Spur API Documentation: https://docs.spur.us/context-api
    Spur Account (API Tokens): https://app.spur.us/account

    TODO: Consider adding tag context as a separate transform.
    '''

    @staticmethod
    def get_maltego_ip_type(ip_in):
        '''
        Returns the Maltego entity type for the given IP address.
        Returns False if the IP address is invalid.
        '''

        try:
            ip_obj = ipaddress.ip_address(ip_in)
            # exclude is_private & 100.64.0.0/10
            if not ip_obj.is_global:
                return False
            if ip_obj.version == 4:
                return 'maltego.IPv4Address'
            elif ip_obj.version == 6:
                return 'maltego.IPv6Address'
        except ValueError:
            return False

    @classmethod
    def create_entities(cls, request: MaltegoMsg, response: MaltegoTransform):
        '''
        Call the Spur Context API and create Maltego entities from the response.
        '''

        # Check if the input is a valid IP address
        try:
            ip_address = request.Value
            # Will raise an exception if not a valid IP address
            ip_address_obj = ipaddress.ip_address(ip_address)
            # Display a message on is_private & 100.64.0.0/10
            if not ip_address_obj.is_global:
                response.addUIMessage(f'{ip_address} is a private IP address.', UIM_TYPES['fatal'])
                return
        except Exception as e:
            response.addUIMessage(f'{e}', UIM_TYPES['fatal'])
            return

        # Accessing the API key from the transform settings
        # api_key = 'example-api-key'
        api_key = request.TransformSettings['api_key']
        # The next line should work according to the docs, but it doesn't
        # api_key = request.getTransformSetting(api_key_setting.id)
        # Spur API is language agnostic
        # language: str = request.getTransformSetting(language_setting.id).lower()
        spur_icon = 'https://spur.us/favicon.ico'

        # May be useful for debugging
        # response.addEntity('maltego.Phrase', ip_address)
        # response.addEntity('maltego.Phrase', api_key)

        try:
            context = get_context_for_ip(ip_address, api_key)

            # AS Number
            asnum = context.get('as',{}).get('number')
            if asnum:
                as_entity = response.addEntity('maltego.AS', asnum)
                as_entity.addProperty(fieldName='organization', displayName='Organization', value=context.get('as',{}).get('organization'))
                as_entity.addProperty(fieldName='spur_icon', value=spur_icon)        
                as_entity.addOverlay('spur_icon', OverlayPosition.NORTH_WEST, OverlayType.IMAGE)

            # Location
                # You can override the location.name value to change the display name, 
                # but then it unsets the value of city and country.
                # order of adding properties is important apparently
            city = context.get('location', {}).get('city')
            state = context.get('location', {}).get('state')
            country_code = context.get('location', {}).get('country')
            location_parts = [part for part in [city, state, country_code] if part is not None]
            location_string = ', '.join(location_parts)
            location_entity = response.addEntity('maltego.Location', f'IP Geo:\n{location_string}')
            location_entity.addProperty(fieldName='city', value=city)
            location_entity.addProperty(fieldName='state', value=state)
            location_entity.addProperty(fieldName='countrycode', value=country_code)
            location_entity.addProperty(fieldName='country', value=country_code)
            location_entity.addProperty(fieldName='spur_icon', value=spur_icon)        
            location_entity.addOverlay('spur_icon', OverlayPosition.NORTH_WEST, OverlayType.IMAGE)

            # Concentration Location
            concentration_city = context.get('client', {}).get('concentration', {}).get('city')
            concentration_state = context.get('client', {}).get('concentration', {}).get('state')
            concentration_country_code = context.get('client', {}).get('concentration', {}).get('country')
            location_parts = [part for part in [concentration_city, concentration_state, concentration_country_code] if part is not None]
            location_string = ', '.join(location_parts)
            if location_string:
                concentration_location_entity = response.addEntity('maltego.Location', f'User Concentration:\n{location_string}')
                concentration_location_entity.addProperty(fieldName='city', value=concentration_city)
                concentration_location_entity.addProperty(fieldName='state', value=concentration_state)
                concentration_location_entity.addProperty(fieldName='countrycode', value=concentration_country_code)
                concentration_location_entity.addProperty(fieldName='country', value=concentration_country_code)
                concentration_location_entity.addProperty(fieldName='density', value=context.get('client', {}).get('concentration', {}).get('density'))
                concentration_location_entity.addProperty(fieldName='geohash', value=context.get('client', {}).get('concentration', {}).get('geohash'))
                concentration_location_entity.addProperty(fieldName='skew', value=context.get('client', {}).get('concentration', {}).get('skew'))
                concentration_location_entity.addProperty(fieldName='spur_icon', value=spur_icon)
                concentration_location_entity.addOverlay('spur_icon', OverlayPosition.NORTH_WEST, OverlayType.IMAGE)

            # Spur Client Context
            client_entity = response.addEntity('maltego.Phrase', f'{ip_address}\nClient Context')
            client_entity.addProperty(fieldName='count', displayName='Count', value=context.get('client', {}).get('count', ''))
            client_entity.addProperty(fieldName='countries', displayName='Countries', value=context.get('client', {}).get('countries', ''))
            client_entity.addProperty(fieldName='spread', displayName='Spread', value=context.get('client', {}).get('spread', ''))
            client_entity.addProperty(fieldName='types', displayName='Types', value=', '.join(context.get('client', {}).get('types', '')))
            client_entity.addProperty(fieldName='proxies', displayName='Proxies', value=', '.join(context.get('client', {}).get('proxies', '')))
            client_entity.addProperty(fieldName='behaviors', displayName='Behaviors', value=', '.join(context.get('client', {}).get('behaviors', '')))
            client_entity.addProperty(fieldName='concentration', displayName='Concentration', value=context.get('client', {}).get('concentration', ''))
            client_entity.setIconURL(spur_icon)

            # Spur Context Tags
            for behavior in context.get('client', {}).get('behaviors', []):
                tag_entity = response.addEntity('maltego.Tag', f'Behavior:\n{behavior}')
                tag_entity.setIconURL(spur_icon)
            for proxy in context.get('client', {}).get('proxies', []):
                tag_entity = response.addEntity('maltego.Tag', f'Proxy:\n{proxy}')
                tag_entity.setIconURL(spur_icon)
            for service in context.get('services', []):
                tag_entity = response.addEntity('maltego.Tag', f'Service:\n{service}')
                tag_entity.setIconURL(spur_icon)
            for risk in context.get('risks', []):
                tag_entity = response.addEntity('maltego.Tag', f'Risk:\n{risk}')
                tag_entity.setIconURL(spur_icon)
            for client_type in context.get('client', {}).get('types', []):
                tag_entity = response.addEntity('maltego.Tag', f'Client Type:\n{client_type}')
                tag_entity.setIconURL(spur_icon)

            # Spur Context Tunnel
            for tunnel in context.get('tunnels', {}):
                tunnel_operator = tunnel.get('operator', 'Operator')
                tunnel_type = tunnel.get('type', 'Type')
                tunnel_entity = response.addEntity('maltego.Phrase', f'{tunnel_type}:\n{tunnel_operator}')
                tunnel_entity.addProperty(fieldName='type', displayName='Type', value=tunnel.get('type', ''))
                tunnel_entity.addProperty(fieldName='entries', displayName='Entries', value=tunnel.get('entries', ''))
                tunnel_entity.addProperty(fieldName='exits', displayName='Exits', value=tunnel.get('exits', ''))
                tunnel_entity.addProperty(fieldName='operator', displayName='Operator', value=tunnel.get('operator', ''))
                tunnel_entity.addProperty(fieldName='anonymous', displayName='Anonymous', value=tunnel.get('anonymous', False))
                tunnel_entity.setLinkColor('#6A48F2')
                tunnel_entity.setLinkLabel(tunnel_type)
                tunnel_entity.setIconURL(spur_icon)
                # Spur Context Tunnel Entry
                for tunnel_entry in tunnel.get('entries', []):
                    entity_type = cls.get_maltego_ip_type(tunnel_entry)
                    if entity_type:
                        entry_entity = response.addEntity(entity_type, tunnel_entry)
                        entry_entity.addProperty(fieldName='tunnel.entry', displayName='Tunnel Entry', value=tunnel_entry)
                        entry_entity.addProperty('tunnelOperator', 'Tunnel Operator', 'loose', tunnel_operator)
                        entry_entity.addOverlay('tunnelOperator', OverlayPosition.WEST, OverlayType.TEXT)
                        entry_entity.addProperty('tunnelEntry', 'Tunnel Entry', 'loose', 'Entry')
                        entry_entity.addOverlay('tunnelEntry', OverlayPosition.SOUTH_WEST, OverlayType.TEXT)
                        entry_entity.addProperty(fieldName='spur_icon', value=spur_icon)        
                        entry_entity.addOverlay('spur_icon', OverlayPosition.NORTH_WEST, OverlayType.IMAGE)
                        entry_entity.setLinkStyle(LINK_STYLE_DASHED)
                        entry_entity.setLinkColor('#6A48F2')
                        entry_entity.setLinkLabel(tunnel_type)
                # Spur Context Tunnel Exit
                for tunnel_exit in tunnel.get('exits', []):
                    entity_type = cls.get_maltego_ip_type(tunnel_exit)
                    if entity_type:
                        exit_entity = response.addEntity(entity_type, tunnel_exit)
                        exit_entity.addProperty(fieldName='tunnel.exit', displayName='Tunnel Exit', value=tunnel_exit)
                        exit_entity.addProperty('tunnelOperator', 'Tunnel Operator', 'loose', tunnel_operator)
                        exit_entity.addOverlay('tunnelOperator', OverlayPosition.WEST, OverlayType.TEXT)
                        exit_entity.addProperty('tunnelExit', 'Tunnel Exit', 'loose', 'Exit')
                        exit_entity.addOverlay('tunnelExit', OverlayPosition.SOUTH_WEST, OverlayType.TEXT)
                        exit_entity.addProperty(fieldName='spur_icon', value=spur_icon)        
                        exit_entity.addOverlay('spur_icon', OverlayPosition.NORTH_WEST, OverlayType.IMAGE)
                        exit_entity.setLinkStyle(LINK_STYLE_DASHED)
                        exit_entity.setLinkColor('#6A48F2')
                        exit_entity.setLinkLabel(tunnel_type)

        except Exception as e:
            response.addUIMessage(f'Error: {e}', UIM_TYPES['fatal'])
