import numpy as np
import matplotlib.pyplot as plt
from gwpy.timeseries import TimeSeries

plt.rcParams.update({# Use mathtext, not LaTeX
                        'text.usetex': False,
                        'axes.formatter.use_mathtext': True,
                        # Use the Computer modern font
                        'font.family': 'serif',
                        'font.serif': 'cmr10',
                        'mathtext.fontset': 'cm',
                        'font.size'   : 20,
                        # Use ASCII minus
                        'axes.unicode_minus': False,
                        'figure.figsize': (15,8) ,
                        })

def plot_spectrogram(frame: str, 
                     channel: str, 
                     time: float, 
                     outseg_before: float = 2.0, 
                     outseg_after: float = 2.0,
                     max_freq: float = 2048.0,
                     min_freq: float = 10.0,
                     q_range: tuple = (4, 64)) -> plt.Figure:
    """
    Plot a spectrogram around a given time and save to output_path.

    Parameters
    ----------
    frame : str
        Path to the frame file to read data from.
    channel : str
        The channel to plot the spectrogram for.
    time : float
        GPS time of the event to plot around.
    outseg_before : float
        Number of seconds before the event time to include in the spectrogram.
    outseg_after : float
        Number of seconds after the event time to include in the spectrogram.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The figure object containing the spectrogram.

    """

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=[21, 10/1.62])
    
    start = time - outseg_before - 10
    end = time + outseg_after + 10

    t1 = TimeSeries.read(frame, channel, start, end, verbose=True)

    qspecgram = t1.q_transform(
            frange=(min_freq, max_freq),
            qrange=q_range,
            outseg=(time - outseg_before, time + outseg_after))

    
    Z = qspecgram.value
    x0 = qspecgram.x0.value  # this is the GPS time corresponding to the start of the q-transform
    xs = np.array([qspecgram.dx.value * i + x0 for i in range(len(Z))])
    xs_rel = xs - time  # subtract central time to center at 0

    y0 = qspecgram.y0.value
    ys = np.array([y0 + qspecgram.dy.value * i for i in range(len(Z[0]))])
    X, Y = np.meshgrid(xs_rel, ys)

    pcm = ax.pcolormesh(X, Y, Z.T, vmin=0, vmax=25, shading='auto')
    ax.set_xlabel(f"Time [s] from {time}")
    ax.set_yscale('log')

    ax.set_ylabel("Frequency [Hz]", labelpad=10)



    return fig
