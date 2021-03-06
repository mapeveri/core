from masonite.exceptions import DriverLibraryNotFound
try:
    import pusher
except ImportError:
    raise DriverLibraryNotFound(
        'Could not find the "pusher" library. Please pip install this library running "pip install pusher"')

class BroadcastPusherDriver(object):

    def __init__(self, BroadcastConfig):
        self.config = BroadcastConfig
        self.ssl_message = True
    
    def ssl(self, boolean):
        self.ssl = ssl_message
        return self

    def channel(self, channels, message, event='base-event'):
        pusher_client = pusher.Pusher(
            app_id=self.config.DRIVERS['pusher']['app_id'],
            key=self.config.DRIVERS['pusher']['client'],
            secret=self.config.DRIVERS['pusher']['secret'],
            ssl=self.ssl_message
        )

        if isinstance(message, str):
            message = {'message': message}  

        if isinstance(channels, list):
            for channel in channels:
                pusher_client.trigger(channel, event, message)
        else:
            pusher_client.trigger(channels, event, message)

        return message

        
