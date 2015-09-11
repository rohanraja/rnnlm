import numpy as np
from colorama import Fore
import theano
import numpy
import os

from theano import tensor as T
from collections import OrderedDict

class RNN():
    
    def __init__(self, nh, ne, de ):
      
        np.random.seed(10)

        # parameters of the model
        self.emb = theano.shared(0.2 * numpy.random.uniform(-1.0, 1.0,\
                   (ne, de)).astype(theano.config.floatX)) # add one for PADDING at the end
        self.Wx  = theano.shared(0.2 * numpy.random.uniform(-1.0, 1.0,\
                   (de, nh)).astype(theano.config.floatX))
        self.Wh  = theano.shared(0.2 * numpy.random.uniform(-1.0, 1.0,\
                   (nh, nh)).astype(theano.config.floatX))
        self.W   = theano.shared(0.2 * numpy.random.uniform(-1.0, 1.0,\
                   (nh, ne)).astype(theano.config.floatX))
        self.bh  = theano.shared(numpy.zeros(nh, dtype=theano.config.floatX))
        self.b   = theano.shared(numpy.zeros(ne, dtype=theano.config.floatX))
        self.h0  = theano.shared(numpy.zeros(nh, dtype=theano.config.floatX))

        # bundle
        self.params = [ self.emb, self.Wx, self.Wh, self.W, self.bh, self.b, self.h0 ]
        self.names  = ['embeddings', 'Wx', 'Wh', 'W', 'bh', 'b', 'h0']

        # Ops definition
        idxs = T.ivector() # as many columns as context window size/lines as words in the sentence
        x = self.emb[idxs].reshape((idxs.shape[0], de))
        y = T.ivector('y')

        def recurrence(x_t, y_t, h_tm1):
            h_t = T.nnet.sigmoid(T.dot(x_t, self.Wx) + T.dot(h_tm1, self.Wh) + self.bh)
            s_t = T.nnet.softmax(T.dot(h_t, self.W) + self.b)
            cost_t = -1.0 *T.log(s_t[0][y_t])
            return [h_t, s_t, cost_t]

        [h, s, costs], _ = theano.scan(fn=recurrence, \
            sequences=[x, y], outputs_info=[self.h0, None, None], \
            n_steps=x.shape[0])

        totalCost = T.mean(costs)
        # y_pred = T.argmax(s[2])
        # y_pred = (s.reshape(idxs.shape[0], ne))
        y_pred = T.argmax(s[:,0,:], axis=1)

        gradients = T.grad( totalCost , self.params )

        lr = T.scalar('lr')
        updates = OrderedDict(( p, p-lr*g ) for p, g in zip( self.params , gradients))

        self.cost = theano.function(inputs=[idxs, y], outputs=totalCost)
        
        # theano functions
        self.classify = theano.function(inputs=[idxs, y], outputs=y_pred)
        #
        self.train = theano.function( inputs  = [idxs, y, lr],
                                      outputs = totalCost,
                                      updates = updates )
        # #
        # self.normalize = theano.function( inputs = [],
        #                  updates = {self.emb:\
        #                  self.emb/T.sqrt((self.emb**2).sum(axis=1)).dimshuffle(0,'x')})



        # import pdb; pdb.set_trace()

    def initializeProcs(self):
        p_y_given_x_lastword = s[-1,0,:]
        p_y_given_x_sentence = s[:,0,:]
        y_pred = T.argmax(p_y_given_x_sentence, axis=1)

        # cost and gradients and learning rate
        lr = T.scalar('lr')
        nll = -T.mean(T.log(p_y_given_x_lastword)[y])
        gradients = T.grad( nll, self.params )
        updates = OrderedDict(( p, p-lr*g ) for p, g in zip( self.params , gradients))
        
        # theano functions
        self.classify = theano.function(inputs=[idxs], outputs=y_pred)

        self.train = theano.function( inputs  = [idxs, y, lr],
                                      outputs = nll,
                                      updates = updates )

        self.normalize = theano.function( inputs = [],
                         updates = {self.emb:\
                         self.emb/T.sqrt((self.emb**2).sum(axis=1)).dimshuffle(0,'x')})
