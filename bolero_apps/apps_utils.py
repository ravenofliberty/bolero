import matplotlib.pyplot as plt
import pandas as pd

BAISC_COLORS = ['#3D8DF5', '#ADCCF7', '#16A163', '#C7EBD1', '#3D8DF5', '#ADCCF7', '#16A163', '#C7EBD1']


def get_figure(df, figsize, legend_cols=1, second_axis=False, second_axis_columns=[], ignore_cols=[], colors_axis_1=[], colors_axis_2=[]):
    df.index = pd.to_datetime(df.index)
    fig, ax1 = plt.subplots(figsize=figsize)

    col_count = 0
    for c in [col for col in df.columns if col not in second_axis_columns and col not in ignore_cols]:
        if len(colors_axis_1) != 0:
            ax1.plot(df[c], label=c, linewidth=2, color=colors_axis_1[col_count])
            col_count += 1
        else:
            ax1.plot(df[c], label=c, linewidth=2)
    ax1.legend(loc="upper left", fontsize=10, ncol=legend_cols)
    ax1.tick_params(axis='x', labelrotation=35, labelsize=10)
    ax1.tick_params(axis='y', labelsize=10)
    ax1.grid()

    if not second_axis and second_axis_columns != []:
        raise KeyError(f'If you want to use second axis set second_axis=True')

    if second_axis and second_axis_columns is not None:
        second_col_count = 0
        ax2 = ax1.twinx()
        if len(colors_axis_2) != 0:
            assert len(second_axis_columns) == len(colors_axis_2), f"When specyfing secondary axis colors they need to " \
                                                                   f"match the length of the secondary axis columns"
        else:
            colors_axis_2 = BAISC_COLORS[:len(second_axis_columns)]
        for c in second_axis_columns:
            if c not in df.columns:
                raise KeyError(f"{c} is not a valid column")
            else:
                ax2.bar(
                    df.index,
                    df[second_axis_columns[0]],
                    0.1,
                    label=second_axis_columns[second_col_count],
                    color=colors_axis_2[second_col_count]
                )
                second_col_count += 1
        ax2.legend(loc='upper right', fontsize=10, ncol=legend_cols)

    return fig