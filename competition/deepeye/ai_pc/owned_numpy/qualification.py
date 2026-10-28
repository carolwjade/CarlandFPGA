"""Fixed FORCE qualification CLI. Source planning does not import actors/model."""
import argparse
import json
from pathlib import Path
import sys
# Fixed sibling package only; no caller-selected source or import factory.
PACKAGE=Path(__file__).absolute().parent
sys.path.insert(0,str(PACKAGE.parent))
from owned_numpy.closure import source_plan,prepare_child

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',action='store_true')
    parser.add_argument('--prepare-child',action='store_true')
    parser.add_argument('--config');parser.add_argument('--config-sha256')
    args=parser.parse_args()
    if args.plan:
        if args.prepare_child or args.config or args.config_sha256:parser.error('--plan accepts no config or mutation')
        _,result=source_plan();print(json.dumps(result,sort_keys=True));return 0
    if not args.config or not args.config_sha256:parser.error('config and raw SHA256 required')
    if args.prepare_child:
        print(json.dumps(prepare_child(args.config,args.config_sha256),sort_keys=True));return 0
    from owned_numpy.provider import OwnedNumpyQualification
    result=OwnedNumpyQualification().run(args.config,args.config_sha256)
    print(json.dumps(result['result'],sort_keys=True))
    return 0 if result['result']['status']=='new_C22_serial_diagnostic_passed' else 1

if __name__=='__main__':
    try:code=main()
    except BaseException as error:
        print(json.dumps(dict(status='refused_or_failed_preserved',type=type(error).__name__,message=str(error)),sort_keys=True));code=2
    sys.exit(code)
