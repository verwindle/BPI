
def apply(func, *args, **kwargs):
    return func(*args, **kwargs)

def ax_plot(plotter, ax, data, name, size, nbins, xscale, yscale):
    '''axes object custom options for sns plots
        plot_axes_attrs: x, y, hue, label e.t.c.'''
    ax.set_xlabel('xlabel', fontsize=size * 1.4, labelpad=size * 1.2)
    ax.set_ylabel('ylabel', fontsize=size * 1.4, labelpad=size * 1.2)
    ax.tick_params('both', pad=size // 1.5)
    ax.locator_params(nbins=nbins, tight=True)
    ax.set_title(f'{plotter.__name__.capitalize()} for {name}', fontsize=size * 2.3, pad=size * 2.4)    
    ax.set_yscale(yscale)
    ax.set_xscale(xscale)
    try:  # tried to modify kwargs; its too hard, so get this)))
        apply(plotter, data=data, **plot_axes_attrs, ax=ax, label=name)
    except TypeError:
        apply(plotter, a=data, **plot_axes_attrs, ax=ax, label=name)
    plt.tight_layout(w_pad=size * .36, h_pad=size * .17)

    
def grid_plot(nrows=2, ncols=2, size=16, nbins=10, xscale='linear', yscale='linear', frameon=True, xrotation=0, yrotation=0):
    '''specify the size and number of axes params and this func will automatically make
        fancy tight layout plot according to the size'''
    wsize = size * ncols
    hsize = size * nrows
    figsize = (1. * wsize, .5 * hsize)
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, frameon=frameon)
    axes = np.array(axes).reshape(-1)
    try:
        gen = (ax_plot(plotter, axes[i], plot_data[i], plot_data_names[i], size, nbins, xscale, yscale) for i in range(axes.shape[0]))
        for g in range(axes.shape[0]): next(gen)
    except IndexError:
        pass
    plt.setp(map(lambda ax: ax.get_xticklabels(), axes), rotation=xrotation);
    plt.setp(map(lambda ax: ax.get_yticklabels(), axes), rotation=yrotation);
    
    return fig
