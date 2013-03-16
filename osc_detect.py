import numpy as np
import datetime
from sunpy.lightcurve import LightCurve
from sunpy.map import MapCube

class BTS():
    """Bayesian Spectral and Parameter Estimation time-series object.
    Accepts SunPy lightcurve objects only.  Will eventually also accept
    mapcube objects """
    def __init__(self, input, **kwargs):
        # Test for input types and get the data out
        # Light curve
        if isinstance(input, LightCurve):
            self.data = input.data.data[:]
            self.index = input.data.index[:]

        # Assume that the last dimension is the time dimension
        # ndarray
        if isinstance(input, np.ndarray):
            self.data = input
            if "index" in kwargs:
                self.index = kwargs.get("index")
            else:
                sh = input.shape
                self.index = np.arange(0, sh[-1]+1 ,1)

        # SunPy mapcubes
        if isinstance(input, MapCube):
            self.data = [m.data for m in input]
            self.index = [m.date for m in input]

        
        # get the times relative to the start time
        if isinstance(self.index[0], datetime.datetime):
            self.time = (self.index[:]-self.index[0]).total_seconds()
        else:
            self.time = self.index[:]-self.index[0]

        # properties of the time-series
        # average cadence
        self.average_cadence = self.time[-1]/(1.0*(len(self.time)-1))

        # regularly spaced FFT frequencies that are >= 0
        _fftfreq=np.fft.fftfreq(len(self.time), self.average_cadence)
        self.fft_frequencies = _fftfreq[_fftfreq>=0.0]
        self.angular_fft_frequencies = 2*np.pi*self.fft_frequencies
        
        # default the analysis frequencies
        self.frequencies = self.fft_frequencies
        self.angular_frequencies = self.angular_fft_frequencies
        
        # number of maps
        self.shape = self.data.shape
        self.nmap = self.shape[-1]

    def where_are_the_low_frequencies(self, limit=0.01):
        """ Returns True for frequencies that are below the low frequency limit"""
        return np.array(self.angular_frequencies*self.time[-1]) < limit

    def get_pdf(self, **kwargs):
        """ Get the normalized probability distribution function for all the 
        frequencies to analyze at.  Returns a mapcube"""
        
        # limit below which we are analyzing at a "low frequency"
        self.limit = kwargs.get("limit", 0.01)
        
        if "frequencies" in kwargs:
            self.frequencies = kwargs.get("frequencies")
            self.angular_frequencies = 2*np.pi*self.frequencies
            cw = _schuster()
        else:
            cw = (np.abs(np.fft.fft(data,axis=-1)))**2
            
        watlf = self.where_are_the_low_frequencies()
        
        
        if "noise_variance" in kwargs:
            pdf = exp(cw/kwargs.get("noise_variance"))
        else:
            d2 = np.mean(self.data^2,axis=-1)
            z = np.zeros(size=cw.shape)
            for i in range(0,self.nmap+1):
                z[:,:,i] = cw[:,:,i]/d2[:,:]
            pdf = (1.0 - 2.0*np.array(z)(1.0*self.nmap)**(1.0-self.nmap/2.0))
        
        # The formulae used are only valid when there is no evidence of a low
        # frequency.  Test for evidence of a low frequency component and issue
        # a warning if it is there.  If not
        total_pdf = np.sum(pdf, axis=-1)
        for i in range(0,self.nmap+1):
            pdf[:,:,i] = pdf[:,:,i]/total_pdf[:,:]

        # The power at each FFT frequency is its own map.  Make a list of maps
        # with the appropriate header and 
        maplist = []
        for i in range(0,self.nmap+1):
            m = Map
            maplist.append(m)
        pdf_mapcube = MapCube(maplist, ordering = self.fft_frequencies)
            
        return pdf_mapcube

    def _schuster(self):
        """Return the Schuster periodogram"""
        
        return cw

    def _known_white_noise(self, white_noise):
        pass
        return
    
    def _unknown_noise(self):
        pass
    
    def detect_regions(self, **kwargs):
        """Detect oscillating regions using the Ireland et al 2010 algorithm.
        Returns a dictionary storing multiple maps of the detected areas, and
        a pandas dataframe describing the properties of each detected region."""
        
        # Get the normalized PDF
        pdf = self.get_pdf(**kwargs)
        
        return