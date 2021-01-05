# -*- coding: utf-8 -*-
import torch
import platform
from copy import deepcopy,copy

import torch.distributed as dist

from parameters import get_args
from components.comps import create_components
from components.optimizer import define_optimizer
from utils.init_config import init_config, init_config_centered
from components.dataset import define_dataset, _load_data_batch
from comms.utils.flow_utils import zero_copy
from nodes.nodes import Client, Server
from comms.trainings.federated import (train_and_validate_federated_centered,
                                       train_and_validate_apfl_centered,
                                       train_and_validate_drfa_centered,
                                       train_and_validate_afl_centered,
                                       train_and_validate_perfedme_centered)
from logs.logging import log, configure_log, log_args
from logs.meter import define_val_tracker
from comms.communication import configure_sync_scheme



def main(args):
    """Non-distributed training."""
    # Create Clients and the Server
    ClientNodes ={}
    for i in range(args.num_workers):
        if args.data in ['emnist','synthetic'] or i==0:
            ClientNodes[i] = Client(args,i)
        else:
            ClientNodes[i] = Client(args,i, Partitioner=ClientNodes[0].Partitioner)
        

    ServerNode = Server(ClientNodes[0].args,ClientNodes[0].model) 
    ServerNode.enable_grad(ClientNodes[0].train_loader)
    # train and evaluate model.
    if ServerNode.args.federated_drfa:
        train_and_validate_drfa_centered(ClientNodes, ServerNode)
    else:
        if ServerNode.args.federated_type == 'apfl':
            train_and_validate_apfl_centered(ClientNodes, ServerNode)
        elif ServerNode.args.federated_type == 'perfedme':
            train_and_validate_perfedme_centered(ClientNodes, ServerNode)
        elif ServerNode.args.federated_type == 'afl':
            train_and_validate_afl_centered(ClientNodes, ServerNode)
        elif ServerNode.args.federated_type in ['fedavg','scaffold','fedgate','qsparse','fedprox','qffl','perfedavg']:
            train_and_validate_federated_centered(ClientNodes, ServerNode)
        else:
            raise NotImplementedError
    return



if __name__ == '__main__':
    args = get_args()
    main(args)