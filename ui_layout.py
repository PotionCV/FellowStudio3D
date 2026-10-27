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
