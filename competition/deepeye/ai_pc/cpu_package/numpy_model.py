"""Fixed real4916-parameter NumPy FORCE CPU model, source version20261028-v1.
Only original finite JSON checkpoint; no pickle, selectable path, fake core,
random initialization, training, quantization, scene or motion API.
"""
import hashlib
import math
from pathlib import Path
import struct
from types import MappingProxyType

from ai_pc.cpu_package import runner as _runner

FIXED_MANIFEST_SHA256='0b76bcd1b21b6b1e254eef0e2e5815a15121fdb8ac48c33710f2b2d85bdf2959'
FIXED_LEAF_SHA256='6547a7a5d1f6d480eec407b66dfbba21656209dff145c027f3e6385141e46ba9'
FIXED_RUNNER_SHA256='92114790259b7e35e8bf7b1a0519f0e3f68da52729d08b5b9862c992deae70af'
FIXED_ORIGINAL_ARCH_SHA256='5003427e1ac01e50b612d8f4f9c674c7df352b3942a5cc39978e23bdfbdb1260'
PREPROCESSING_SHA256='cb66fd302165c86344f3b8d1af9d9c4e4e229621cef44cbfa6fb8cd121a63eef'
LABEL_SCHEMA_SHA256='0913ff5a59085b47802a9902f23a836f4fa1129700de8e6593840416f4d7beed'
CLASS_ORDER=(30000,65030,65000,80000,74000,70000,70032,88000,86000,99000,90000,93000)
GRAPH=[{'name':'conv1','op':'Conv2D','in_channels':8,'out_channels':16,'kernel':[5,1],'padding':[2,0]},
 {'name':'relu1','op':'ReLU'},{'name':'pool1','op':'AvgPool2D','kernel':[4,1],'stride':[4,1]},
 {'name':'conv2','op':'Conv2D','in_channels':16,'out_channels':24,'kernel':[5,1],'padding':[2,0]},
 {'name':'relu2','op':'ReLU'},{'name':'pool2','op':'AvgPool2D','kernel':[4,1],'stride':[4,1]},
 {'name':'flatten','op':'Flatten','start_dim':1},{'name':'head','op':'Gemm','in_features':192,'out_features':12}]

class NumpyModelError(ValueError): pass

def need(value,message):
    if value is not True:raise NumpyModelError(message)

def typed_equal(left,right):
    if type(left) is not type(right):return False
    if type(left) is dict:return left.keys()==right.keys() and all(typed_equal(left[key],right[key]) for key in left)
    if type(left) is list:return len(left)==len(right) and all(typed_equal(a,b) for a,b in zip(left,right))
    return left==right

def _pinned(path,expected):
    return _runner.read_pinned(path,expected,limit=2*1024*1024)

def _document(path,expected):return _runner.strict_json(_pinned(path,expected))

def _reference(base,record,expected):
    need(type(record) is dict and record.keys()=={'path','sha256'},'exact fixed asset reference required')
    need(type(record['path']) is str and type(record['sha256']) is str and len(record['sha256'])==64 and all(c in '0123456789abcdef' for c in record['sha256']),'fixed asset path/hash invalid')
    actual=(base/record['path']).resolve()
    need(actual==expected.resolve(),'asset must resolve to exact original fixed path')
    return actual

class NumpyForceModel:
    __slots__=('__leaf','__parameters','__pins','__forward_attempts')
    def __init__(self):
        product=Path(__file__).resolve().parents[2]
        manifest_path=product/'ai_pc/cpu_model/force_v1/model_manifest.json'
        _pinned(Path(_runner.__file__),FIXED_RUNNER_SHA256)
        _pinned(Path(__file__).with_name('numpy_leaf.py'),FIXED_LEAF_SHA256)
        from ai_pc.cpu_package import numpy_leaf as leaf
        need(Path(leaf.__file__).resolve()==Path(__file__).with_name('numpy_leaf.py').resolve(),'fixed NumPy leaf origin required')
        manifest=_document(manifest_path,FIXED_MANIFEST_SHA256)
        required={'schema_version','model_id','profile_id','source_domain','input_shape','class_order','graph','weights','preprocessing','label_schema','training','scope'}
        need(type(manifest) is dict and manifest.keys()==required and type(manifest['schema_version']) is int and manifest['schema_version']==1,'original model manifest schema invalid')
        need((manifest['model_id'],manifest['profile_id'],manifest['source_domain'])==('force-cnn-cpu-v1-20261024','force_curve_v1','geo_replay'),'fixed model/profile/domain required')
        need(typed_equal(manifest['input_shape'],['N',8,128,1]) and typed_equal(manifest['class_order'],list(CLASS_ORDER)),'original full graph shape/classes required')
        need(type(manifest['training']) is dict and type(manifest['scope']) is dict,'original model metadata required')
        base=manifest_path.parent
        graph_path=_reference(base,manifest['graph'],base/'graph.json');graph=_document(graph_path,manifest['graph']['sha256'])
        need(type(graph) is dict and graph.keys()=={'format','input_shape','output_shape','layers','parameters','source'} and graph['format']=='fixed-force-cnn-graph-v1','original graph metadata invalid')
        need(type(graph['parameters']) is int and graph['parameters']==4916 and typed_equal(graph['layers'],GRAPH) and typed_equal(graph['input_shape'],['N',8,128,1]) and typed_equal(graph['output_shape'],['N',12]),'no reduced/replaced graph allowed')
        architecture=_reference(base,graph['source'],product/'ai_pc/model/force_cnn.py')
        need(graph['source']['sha256']==FIXED_ORIGINAL_ARCH_SHA256,'original architecture lineage SHA changed')
        _pinned(architecture,FIXED_ORIGINAL_ARCH_SHA256)  # Source bytes only; never import Torch architecture.
        for field,name,fixed_sha in (('preprocessing','preprocessing.json',PREPROCESSING_SHA256),('label_schema','label_schema.json',LABEL_SCHEMA_SHA256)):
            source=_reference(base,manifest[field],product/'data'/name)
            need(manifest[field]['sha256']==fixed_sha,'original preprocessing/label pin changed')
            data=_document(source,fixed_sha)
            if field=='label_schema':need([row['source_code'] for row in data['classes']]==list(CLASS_ORDER),'original label order changed')
        weights_path=_reference(base,manifest['weights'],base/'weights.json')
        encoded=_document(weights_path,manifest['weights']['sha256'])
        need(type(encoded) is dict and encoded.keys()=={'format','tensors'} and encoded['format']=='finite-float32-state-dict-json-v1','original JSON checkpoint format required')
        tensors=encoded['tensors'];need(type(tensors) is dict and tensors.keys()==leaf.SHAPES.keys(),'exact original six learned tensors required')
        state={};count=0
        for name,shape in leaf.SHAPES.items():
            record=tensors[name]
            need(type(record) is dict and record.keys()=={'shape','values'} and typed_equal(record['shape'],list(shape)),'original tensor shape invalid: '+name)
            values=record['values'];size=math.prod(shape)
            need(type(values) is list and len(values)==size,'original tensor count invalid: '+name)
            try:finite=all(type(value) in (int,float) and math.isfinite(value) for value in values)
            except OverflowError:finite=False
            need(finite,'original checkpoint nonfinite/type invalid: '+name)
            with leaf.np.errstate(all='ignore'):array=leaf.np.asarray(values,dtype=leaf.np.float32).reshape(shape)
            leaf._array(array,shape,name);array.flags.writeable=False;state[name]=array;count+=size
        need(count==4916,'all learned parameters required')
        self.__leaf=leaf;self.__parameters=MappingProxyType(state);self.__forward_attempts=0
        self.__pins={'numpy_backend_id':leaf.BACKEND_ID,'numpy_leaf_source_sha256':FIXED_LEAF_SHA256,
            'numpy_model_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'numpy_blas_thread_policy':'env1-einsum-optimize-false-no-dot-no-matmul',
            'original_architecture_lineage_sha256':FIXED_ORIGINAL_ARCH_SHA256}

    @property
    def class_order(self):return CLASS_ORDER

    def backend_pins(self):return dict(self.__pins)

    def ready_description(self):
        import os
        return {'backend_id':self.__leaf.BACKEND_ID,'numpy_version':self.__leaf.np.__version__,
            'parameter_count':sum(value.size for value in self.__parameters.values()),
            'all_float32_readonly':all(value.dtype==self.__leaf.np.dtype('float32') and not value.flags.writeable for value in self.__parameters.values()),
            'thread_environment':{name:os.environ.get(name) for name in self.__leaf.THREAD_ENV},
            'BLAS_worker_count_measured':False,'dot_or_matmul_in_numeric_leaf':False,
            'forward_attempts':self.__forward_attempts,'source_pins':dict(self.__pins)}

    def tensor(self,window):
        with self.__leaf.np.errstate(all='ignore'):tensor=self.__leaf.np.asarray(window.to_model_input(),dtype=self.__leaf.np.float32,order='C')
        try:self.__leaf._array(tensor,(1,8,128,1),'input')
        except ValueError as error:raise _runner.PackageError('feature_invalid','float32 model input must be finite [1,8,128,1]') from error
        packed=struct.pack('<1024f',*tensor.reshape(-1).tolist())
        return tensor,hashlib.sha256(packed).hexdigest()

    def tensor_fingerprints(self):
        # Readable loaded float32 bits for Root parity; no weights/output factory.
        return {name:{'shape':list(value.shape),'dtype':'float32','order':'C',
            'bytes':value.size*4,'sha256':hashlib.sha256(value.astype('<f4',copy=False).tobytes(order='C')).hexdigest()}
            for name,value in self.__parameters.items()}

    def evaluate_once(self,tensor):
        # Root diagnostic logits and probabilities share ONE full graph call.
        self.__forward_attempts+=1
        try:
            logits=self.__leaf.forward_logits_float32(tensor,self.__parameters)
            probabilities=self.__leaf.stable_softmax_float32(logits)
        except (ValueError,FloatingPointError) as error:
            raise _runner.PackageError('model_output_invalid','fixed NumPy model must return finite normalized [1,12] probabilities') from error
        return logits,probabilities

    def predict(self,tensor):
        _logits,probabilities=self.evaluate_once(tensor)
        return probabilities[0].tolist()
