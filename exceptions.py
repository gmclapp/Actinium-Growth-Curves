class BadDatesError(Exception):
    '''Exception raised when dates in dataframe are out of order.'''
    def __init__(self, sourceName=""):
        self.message = "Dates in data source {} are out of order.".format(sourceName)
        super().__init__(self.message)
        
