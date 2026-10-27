"""Layout budgets in Tk logical pixels (never physical Retina pixels)."""
import math


def fitted_scale(preferred, width, height):
    limit=min((width-48)/960,(height-96)/560)
    limit=math.floor((limit+1e-6)*20)/20
    return max(.75,min(2.,preferred,limit))


def panel_sizes(width, scale, preferred):
    left_min=max(150,round(170*min(scale,1.2)))
    right_min=max(180,round(200*min(scale,1.2)))
    center=max(280,min(520,round(width*.44)))
    budget=max(left_min+right_min,min(round(width*.52),width-center-64))
    wanted=[max(left_min,round(preferred[0]*scale)),max(right_min,round(preferred[1]*scale))]
    extra=max(0,budget-left_min-right_min)
    demand=[wanted[0]-left_min,wanted[1]-right_min]
    factor=min(1,extra/max(1,sum(demand)))
    return left_min+round(demand[0]*factor),right_min+round(demand[1]*factor),left_min,right_min


def preview_fitted_scale(scale, width, height, window_width, window_height):
    """Reduce only after measuring the settled canvas, including wrapped toolbars.

    Keep a useful preview on small displays without replacing the user's
    preferred scale. Small steps allow controls to reflow before measuring again.
    """
    target_width=min(480,max(280,window_width*.36))
    target_height=min(360,max(220,window_height*.38))
    if width>=target_width and height>=target_height:
        return scale
    return max(.75,round(scale-.1,2))
