#  Copyright (c) maiot GmbH 2020. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.

from zenml.core.steps.deployer.base_deployer import BaseDeployerStep

try:
    from zenml.core.steps.deployer.cortex_deployer import CortexDeployer
except ModuleNotFoundError:
    pass

from zenml.core.steps.deployer.gcaip_deployer import GCAIPDeployer