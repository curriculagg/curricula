class Singleton(type):
    """Singleton metaclass."""

    __instances = {}

    def __call__(cls, *args, **kwargs):
        """Instantiate if not in the map, otherwise return existing."""

        if cls not in cls.__instances:
            cls.__instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.__instances[cls]
