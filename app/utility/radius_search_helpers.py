import pandas as pd
from typing import List, Tuple

def multi_radius_search(
    public_df: pd.DataFrame,
    private_df: pd.DataFrame,
    number_institutions: int,
    city_not_specified: bool,
    radii: List[int] = [5, 10, 20, 50, 100, 200, 500]
) -> Tuple[pd.DataFrame, pd.DataFrame, int]:
    """
    Try increasing radii to get enough institutions. Returns filtered public/private dfs and the used radius.
    If city_not_specified is True, returns original dfs and radius 0.
    """
    if city_not_specified:
        return public_df, private_df, 0
    for radius in radii:
        pub = public_df[public_df['Distance'] <= radius] if 'Distance' in public_df.columns else public_df
        priv = private_df[private_df['Distance'] <= radius] if 'Distance' in private_df.columns else private_df
        if len(pub) >= number_institutions or len(priv) >= number_institutions:
            return pub, priv, radius
    # If none of the radii yield enough, return the largest radius result
    if 'Distance' in public_df.columns:
        pub = public_df[public_df['Distance'] <= radii[-1]]
    else:
        pub = public_df
    if 'Distance' in private_df.columns:
        priv = private_df[private_df['Distance'] <= radii[-1]]
    else:
        priv = private_df
    return pub, priv, radii[-1]
