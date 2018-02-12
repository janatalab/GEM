'''
A priori power analysis for single player GEM experiment.

This experiment involves solo tapper with adaptive metronome to make
sure that we can replicate the single-tapper results of Fairhurst, Janata, and
Keller, 2012, with the GEM system. The original Fairhurst et al. paper and
supplemental information are available here:
https://doi.org/10.1093/cercor/bhs243

GEM project details:
Authors: Lauren Fink, Scottie Alexander, Petr Janata
Contact: pjanata@ucdavis.edu
Repository link: https://github.com/janatalab/GEM
'''

from numpy import sqrt
from math import ceil

# The effect size we want to detect is the difference between metronome
# alpha=0 and alpha=0.25. Let's get our estimates from Fairhurst et al. (2012).
# Like them, we plan to use repeated measures ANOVA.

# -----------------------------------------------------------------------------# 
# Mean and SE of Behavioural Data from Fairhurst et al. (2012)
# Supplemental Information.
# -----------------------------------------------------------------------------# 
# VP adaptivity (α)   Mean Asynchrony (ms)    SD Asynchrony (ms)
# 0                   -26.70±3.43             23.64±1.91
# 0.25                -23.18±2.88             21.41±1.90
# 0.5                 -21.33±2.76             22.09±2.21
# 0.75                -20.79±2.31             24.09±2.55
# 1                   -18.39±3.23             28.74±3.10

# -----------------------------------------------------------------------------#
                        # Estimate Effect Size
# -----------------------------------------------------------------------------#
# Effect size: mean(treatment) - mean(control) / std(control)
# TODO: should we use mean or SD asych?

# If SD:
pooledSD = sqrt(1.91**2 + 1.90**2 / 2)
ES = (21.41 - 23.64) / pooledSD

# If want to use mean:
# pooledSD = np.sqrt(3.43**2 + 2.88**2 / 2)
# ES = (23.18 - 26.7) / pooledSD

# -----------------------------------------------------------------------------#
                        # Set desired alpha and power
# -----------------------------------------------------------------------------#
# alpha = .05
# power = .90

# Look up appropriate Z values for these desired parameters
Zalpha = 1.96
Zpower = 1.282 #.84 = 80%

# -----------------------------------------------------------------------------#
                        # Determine sample size required
# -----------------------------------------------------------------------------#
# compute N, given the above parameters
N = ((Zalpha + Zpower) / ES) **2
N = ceil(N)

# -----------------------------------------------------------------------------#
                        # Example write-up of power analysis
# -----------------------------------------------------------------------------#
# A statistical power analysis was performed for sample size estimation, based
# on data from Fairhurst et al. (2012) (N=16), comparing metronome
# adaptivity = 0 to metronome adaptivity =.25. The effect size (ES) in this
# study was -.95, considered to be large using Cohen's (1988) criteria.
# With an alpha = .05 and power = 0.90, the projected sample size
# needed with this effect size is approximately N = 12 for this simplest
# comparison between conditions. Thus, our proposed sample size of 20 will be
# more than adequate for the main objective of this study and should also allow
# for expected attrition.


# If use mean instead of SD asynchony, N = 14
