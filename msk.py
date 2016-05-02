def afsk2400(bits, fs = 48000, mark_f = 1200, space_f = 2400, baud = 2400):
    # the function will take a bitarray of bits and will output an AFSK1200 modulated signal of them
    #  Inputs:
    #         bits  - bitarray of bits
    #         fs    - sampling rate
    # Outputs:
    #         sig    -  returns afsk2400 modulated signal
    fs_lcm = lcm((baud, fs))

    fc = (mark_f+space_f)/2
    df = (mark_f-space_f)/2

    Ns = fs_lcm/baud
    mark_f = np.empty(0)

    N = Ns*len(bits)

    for i in bits:
        mark_f = np.r_[mark_f, np.repeat(1 if i else -1, Ns)]

    t = np.linspace(0,len(bits)*1.0/baud,N-1)

    phase = 2*pi*fc*t + 2*pi*df*integrate.cumtrapz(mark_f*(1.0/fs_lcm))
    sig = np.cos(phase)

    return sig[::fs_lcm/fs]

def nc_afsk2400Demod(sig, fs=48000.0, mark_f=1200, space_f=2400 baud=2400, TBW=2.0, bp_BW = 1600, lp_BW = 1200, lpp_BW = 2400):
    #  non-coherent demodulation of afsk1200
    # function returns the NRZ (without rectifying it)
    #
    # sig  - signal
    # fs   - sampling rate in Hz
    # mark_f - mark frequency
    # space_f - space frequency
    # baud - The bitrate. Default 1200
    # TBW  - TBW product of the filters
    # bp_BW - pre BP filter twosided bandwith
    # lp_BW - frequency selectors twosided bandwith
    # lpp_BW - post LP filter twosided bandwith
    #
    # Returns:
    #     NRZ
    N = (fs*TBW*1.0/lp_BW // 2) * 2 + 1

    # BP Filter
    h_bp = np.exp(1j*2*pi*(mark_f+space_f)/2, signal.firwin(N, bp_BW/2, nyq=fs/2, window='hanning')

    # Find Space and Mark
    h = signal.firwin(N, lp_BW/2, nyq=fs/2, window='hanning')

    h_s = np.exp(1j*2*pi*np.arange(N)*space_f/fs) * h
    h_m = np.exp(1j*2*pi*np.arange(N)*mark_f/fs) * h

    space = signal.fftconvolve(sig, h_s, mode='same')
    mark = signal.fftconvolve(sig, h_m, mode='same')
    NRZ = np.abs(space) - np.abs(mark)

    # Post LP Filter

    return NRZ