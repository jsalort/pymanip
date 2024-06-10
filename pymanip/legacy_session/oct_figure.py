"""Read Octave Figure file (:mod:`pymanip.legacy_session.oct_figure`)
=====================================================================

.. autofunction:: openfig

"""
import matplotlib.pyplot as plt
from pymanip.legacy_session.octmi_binary import read_octave_binary


def openfig(filename):
    """Create a Matplotlib figure from a GNU Octave Figure file.

    :param filename: path to input ofig file.
    :type filename: str
    :return: fig, axes
    :rtype: :class:`~matplotlib.figure.Figure`, list
    """
    fig_handle = read_octave_binary(filename)["s_oct40"]
    if fig_handle["type"] == "figure":
        # properties = fig_handle["properties"]
        fig = plt.figure()
        axes = list()
        children = fig_handle["children"]
        for child_index, child_type in enumerate(children["type"]):
            if child_type == "axes":
                ax_properties = children["properties"][child_index]
                ax_children = children["children"][child_index]
                ax = fig.add_subplot(1, 1, 1)
                axes.append(ax)
                # clim = ax_properties['clim']
                # cmap = ax_properties['colormap']
                # color_order = ax_properties['colororder']
                # color_order_index = ax_properties['colororderindex']
                # grid_color = ax_properties['grid_color']
                xscale = ax_properties["xscale"]
                yscale = ax_properties["yscale"]
                xticks = ax_properties["xtick"]
                xticklabels = ax_properties["xticklabel"]
                yticks = ax_properties["ytick"]
                yticklabels = ax_properties["yticklabel"]
                xlim = ax_properties["xlim"]
                ylim = ax_properties["ylim"]
                for ax_child_index, ax_child_type in enumerate(ax_children["type"]):
                    if ax_child_type == "line":
                        line_properties = ax_children["properties"][ax_child_index]
                        marker = line_properties["marker"]
                        markeredgecolor = line_properties["markeredgecolor"]
                        markerfacecolor = line_properties["markerfacecolor"]
                        markersize = line_properties["markersize"]
                        linestyle = line_properties["linestyle"]
                        linewidth = line_properties["linewidth"]
                        color = line_properties["color"]
                        xdata = line_properties["xdata"]
                        ydata = line_properties["ydata"]
                        if marker and str(markerfacecolor) == "none":
                            markerfacecolor = "white"
                        ax.plot(
                            xdata,
                            ydata,
                            f"{marker if marker != 'none' else ''}{linestyle if linestyle != 'none' else ''}",
                            color=color,
                            mec=markeredgecolor
                            if (
                                marker != "none"
                                and str(markeredgecolor) not in ["auto", "none"]
                            )
                            else None,
                            mfc=markerfacecolor
                            if (
                                marker != "none"
                                and str(markerfacecolor) not in ["auto", "none"]
                            )
                            else None,
                            markersize=markersize
                            if (marker != "none" and markersize)
                            else None,
                            linewidth=linewidth if linewidth != 0 else None,
                        )
                    elif ax_child_type == "text":
                        text_properties = ax_children["properties"][ax_child_index]
                        if text_properties["__autopos_tag__"] == "xlabel":
                            ax.set_xlabel(text_properties["string"])
                        elif text_properties["__autopos_tag__"] == "ylabel":
                            ax.set_ylabel(text_properties["string"])
                        elif (
                            text_properties["__autopos_tag__"] == "zlabel"
                            and text_properties["string"]
                        ):
                            ax.set_zlabel(text_properties["string"])
                        elif (
                            text_properties["__autopos_tag__"] == "title"
                            and text_properties["string"]
                        ):
                            ax.set_title(text_properties["string"])
                    else:
                        print(f"Ignoring ax child type {ax_child_type}")
                ax.set_xscale(xscale)
                ax.set_yscale(yscale)
                ax.set_xticks(xticks)
                ax.set_xticklabels(xticklabels)
                ax.set_yticks(yticks)
                ax.set_yticklabels(yticklabels)
                ax.set_xlim(xlim)
                ax.set_ylim(ylim)
            else:
                print(f"Ignoring child type {child_type}")

    else:
        raise ValueError(f"Unknown type {fig_handle['type']}")

    return fig, axes
