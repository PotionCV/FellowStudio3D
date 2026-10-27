"""Layout budgets in Tk logical pixels (never physical Retina pixels)."""


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


def preview_fitted_scale(scale, width, height, window_width, window_height, recovering=False):
    """Emergency fallback, measured after layout; no window-size scale cap.

    Enter only below 240x140 logical pixels. Once entered, recover to 280x180
    before stopping, so one borderline pixel does not retrigger shrinking.
    """
    # One-pixel construction measurements are not evidence that a normal
    # desktop window lacks space. A genuinely short, settled viewport still
    # needs the fallback regardless of OS or screen resolution.
    if window_width>=1280 and window_height>=800 and min(width,height)<=1:return scale
    target_width,target_height=(280,180) if recovering else (240,140)
    if width>=target_width and height>=target_height:return scale
    return max(.75,round(scale-.1,2))
