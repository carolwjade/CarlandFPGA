"""Real full fixed FORCE CNN numerical leaf, NumPy CPU float32 version1.
No files, checkpoints, model construction, callbacks, selector or training API.
Only new synthetic definition controls may call this leaf without fixed loader.
"""
from collections.abc import Mapping
import os

THREAD_ENV=('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS')
if any(os.environ.get(name)!='1' for name in THREAD_ENV):
    raise ValueError('explicit pre-import BLAS/thread policy1 required')
import numpy as np
if np.__version__!='2.5.4': raise ValueError('exact NumPy2.5.4 required')

BACKEND_ID='numpy-2.5.4-cpu-float32-einsum-optimize-false-v1'
SHAPES={'conv1.weight':(16,8,5,1),'conv1.bias':(16,),
        'conv2.weight':(24,16,5,1),'conv2.bias':(24,),
        'head.weight':(12,192),'head.bias':(12,)}

def _array(value,shape,label):
    if type(value) is not np.ndarray or value.dtype!=np.dtype('float32') or not value.dtype.isnative or value.shape!=shape or not value.flags.c_contiguous:
        raise ValueError(label+' requires exact native float32 C-order fixed shape')
    if not bool(np.isfinite(value).all()): raise ValueError(label+' must be finite')
    return value

def _parameters(tensors):
    if not isinstance(tensors,Mapping) or set(tensors)!=set(SHAPES): raise ValueError('exact six fixed parameter tensors required')
    for name,shape in SHAPES.items(): _array(tensors[name],shape,name)

def _conv5_same(x,weight,bias):
    height=x.shape[2]
    padded=np.zeros((1,x.shape[1],height+4,1),dtype=np.float32)
    padded[:,:,2:height+2,:]=x
    result=np.empty((1,weight.shape[0],height,1),dtype=np.float32)
    # Cross-correlation: x[t+k-2]*weight[o,i,k,0], no kernel reversal.
    for t in range(height):
        result[:,:,t,0]=np.einsum('nik,oik->no',padded[:,:,t:t+5,0],weight[:,:,:,0],dtype=np.float32,optimize=False)+bias
    return result

def _pool4(x):
    return x.reshape(1,x.shape[1],x.shape[2]//4,4,1).mean(axis=3,dtype=np.float32)

def forward_logits_float32(values,tensors):
    x=_array(values,(1,8,128,1),'input');_parameters(tensors)
    # Match Torch's final-finite boundary; do not add clipping or silently
    # replace nonfinite intermediates. ReLU alone is the model's max(0,x).
    with np.errstate(all='ignore'):
        x=_pool4(np.maximum(_conv5_same(x,tensors['conv1.weight'],tensors['conv1.bias']),np.float32(0)))
        x=_pool4(np.maximum(_conv5_same(x,tensors['conv2.weight'],tensors['conv2.bias']),np.float32(0)))
        flat=x.reshape(1,192,order='C')
        logits=np.einsum('ni,oi->no',flat,tensors['head.weight'],dtype=np.float32,optimize=False)+tensors['head.bias']
    return _array(logits,(1,12),'logits')

def stable_softmax_float32(logits):
    logits=_array(logits,(1,12),'logits')
    with np.errstate(all='ignore'):
        shifted=logits-np.max(logits,axis=1,keepdims=True)
        exponentials=np.exp(shifted)
        denominator=np.sum(exponentials,axis=1,keepdims=True,dtype=np.float32)
        probabilities=exponentials/denominator
    probabilities=_array(probabilities,(1,12),'probabilities')
    if bool((probabilities<0).any()) or bool((probabilities>1).any()):raise ValueError('probability outside[0,1]')
    if abs(sum(float(value) for value in probabilities[0])-1.0)>1e-5:raise ValueError('probabilities do not sum to one')
    return probabilities

def predict_float32(values,tensors):
    return stable_softmax_float32(forward_logits_float32(values,tensors))
