"""
ComfyUI constants - Samplers and Schedulers

These constants are extracted from ComfyUI's samplers.py
Reference: ComfyUI/comfy/samplers.py lines 730-734, 1054, 1063-1074

Note: This module uses the full ComfyUI installation from backend/ComfyUI/
"""

# All available samplers in ComfyUI
# From KSAMPLER_NAMES + ["ddim", "uni_pc", "uni_pc_bh2"]
SAMPLER_NAMES = [
    # K-diffusion samplers (basic)
    "euler",
    "euler_cfg_pp",
    "euler_ancestral",
    "euler_ancestral_cfg_pp",
    "heun",
    "heunpp2",

    # DPM samplers
    "dpm_2",
    "dpm_2_ancestral",
    "dpm_fast",
    "dpm_adaptive",

    # DPM++ samplers
    "dpmpp_2s_ancestral",
    "dpmpp_2s_ancestral_cfg_pp",
    "dpmpp_sde",
    "dpmpp_sde_gpu",
    "dpmpp_2m",
    "dpmpp_2m_cfg_pp",
    "dpmpp_2m_sde",
    "dpmpp_2m_sde_gpu",
    "dpmpp_3m_sde",
    "dpmpp_3m_sde_gpu",

    # Other samplers
    "lms",
    "ddpm",
    "ddim",
    "lcm",

    # Advanced samplers
    "ipndm",
    "ipndm_v",
    "deis",
    "uni_pc",
    "uni_pc_bh2",

    # Resolution samplers
    "res_multistep",
    "res_multistep_cfg_pp",
    "res_multistep_ancestral",
    "res_multistep_ancestral_cfg_pp",

    # Experimental samplers
    "gradient_estimation",
    "gradient_estimation_cfg_pp",
    "er_sde",
    "seeds_2",
    "seeds_3",

    # SA Solver
    "sa_solver",
    "sa_solver_pece"
]

# All available schedulers in ComfyUI
# From SCHEDULER_HANDLERS keys
SCHEDULER_NAMES = [
    "simple",           # Simple linear scheduler
    "normal",           # Normal scheduler
    "sgm_uniform",      # SGM uniform scheduler (default in many cases)
    "ddim_uniform",     # DDIM uniform scheduler
    "karras",           # Karras noise schedule (popular for high quality)
    "exponential",      # Exponential noise schedule
    "beta",             # Beta distribution scheduler
    "linear_quadratic", # Linear-quadratic scheduler (for video models)
    "kl_optimal"        # KL-optimal scheduler
]

# Recommended samplers (most commonly used and tested)
RECOMMENDED_SAMPLERS = [
    "euler",
    "euler_ancestral",
    "heun",
    "dpm_2",
    "dpm_2_ancestral",
    "dpmpp_2m",
    "dpmpp_2m_sde",
    "dpmpp_2m_sde_gpu",
    "dpmpp_3m_sde",
    "dpmpp_sde",
    "ddim",
    "uni_pc",
    "lcm"
]

# Recommended schedulers (most commonly used)
RECOMMENDED_SCHEDULERS = [
    "normal",
    "karras",
    "exponential",
    "sgm_uniform",
    "simple"
]

# Samplers that work well with specific schedulers
SAMPLER_SCHEDULER_RECOMMENDATIONS = {
    "euler": ["normal", "karras", "exponential"],
    "euler_ancestral": ["normal", "karras", "exponential"],
    "dpmpp_2m": ["karras", "exponential", "normal"],
    "dpmpp_2m_sde": ["karras", "exponential"],
    "dpmpp_3m_sde": ["exponential", "karras"],
    "ddim": ["ddim_uniform", "normal"],
    "uni_pc": ["karras", "normal"],
}

