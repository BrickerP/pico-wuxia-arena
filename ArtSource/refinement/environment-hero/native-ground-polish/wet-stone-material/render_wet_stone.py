"""Use the frozen ground-review camera and lighting with the PNG-equivalent full scene."""
from pathlib import Path
import importlib.util
import sys

HERE=Path(__file__).resolve().parent;GROUND=HERE.parent
spec=importlib.util.spec_from_file_location('ground_render',GROUND/'render_ground.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.HERE=HERE
module.OUT=HERE/'review'
module.SOURCE=GROUND.parent/'native-fight-entrance/courtyard_native_entrance.glb'
module.CANDIDATE=HERE/'courtyard_wet_stone_png.glb'
module.SOURCE_SHA='96c554cc73bfe4b654cc9045e3d0f6464838c6a7517f59da0dd4bb8c65ab242d'
# Reproduce the original reviewed actor, not whichever model is deployed today.
FROZEN_ACTOR=module.ROOT/'ArtSource/refinement/combat-direction/native-weighted-overhead/integration/candidate-library-v5'
module.ACTOR=FROZEN_ACTOR/'base_prepared_png.glb'
module.RUNTIME_ACTOR=FROZEN_ACTOR/'base.glb'
module.ENCODING=FROZEN_ACTOR/'base_texture_encoding.json'
module.ALIGNMENT=FROZEN_ACTOR/'base_alignment.json'
if __name__=='__main__':
    actor=module.actor_identity(False)
    if not actor.get('included'):
        raise ValueError('Frozen historical actor inputs must be restored before reproduction: '+actor.get('exclusion_reason','unknown'))
    module.main()
