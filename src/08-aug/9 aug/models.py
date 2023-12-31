import torch
import torch.nn as nn
import pytorch_lightning
import torchmetrics

Universal_Apprioximate_Function = 49
class Baseline(torch.nn.Module):
    def __init__(self):
        super().__init__()
        # Reshape in forward here
        self.layer_1         = nn.Linear(28*28,Universal_Apprioximate_Function)
        self.class_predictor = nn.Linear(Universal_Apprioximate_Function, 10)

    def forward(self, X):
        X      = X.view(-1,28*28)
        output = self.layer_1(X)
        output = nn.functional.relu(output)

        output       = self.class_predictor(output)
        output_probs = nn.functional.softmax(output, dim=1)
        output_class = torch.argmax(output_probs, dim=1)

        return output_probs

class Extended(pytorch_lightning.LightningModule):
    def __init__(self, init_model: torch.nn.Module):
        super().__init__()
        self.automatic_optimization = False
        self.pytorch_model = init_model

        self.train_acc  = torchmetrics.Accuracy(task="multiclass", num_classes=10)
        self.val_acc    = torchmetrics.Accuracy(task="multiclass", num_classes=10)
    
    def forward(self, X):
        return self.pytorch_model(X)

    def training_step(self, batch_XY, batch_no):
        X, Y = batch_XY
        optimizer = self.optimizers()
        
        Y_predicted_probs   = self.pytorch_model(X)
        loss = nn.functional.cross_entropy(Y_predicted_probs, Y)
        self.manual_backward(loss)
        optimizer.step()

        self.log("train loss",loss.item(), on_step=True, prog_bar=True)
        Y_predicted_labels  = torch.argmax(Y_predicted_probs, dim = 1, keepdim = True )
        Y_actual_labels     = torch.argmax(Y, dim = 1, keepdim = True)
        accuracy = self.train_acc(Y_predicted_labels,Y_actual_labels)
        self.log("train accuracy",accuracy , on_step=True, prog_bar=True)
        tensorboard = self.logger.experiment

        optimizer.zero_grad()

    def validation_step(self, batch_XY, batch_no):
        X, Y = batch_XY
        Y_predicted_probs = self.pytorch_model(X)
        loss = nn.functional.cross_entropy(Y_predicted_probs, Y)
        self.log("validation loss",loss.item(), prog_bar=True)

        Y_predicted_labels  = torch.argmax(Y_predicted_probs, dim = 1, keepdim = True )
        Y_actual_labels     = torch.argmax(Y, dim = 1, keepdim = True)
        accuracy = self.train_acc(Y_predicted_labels,Y_actual_labels)
        self.log("validation accuracy",accuracy , prog_bar=True)

    def configure_optimizers(self):
        W_PARAMETERS = self.pytorch_model.parameters()
        optimizer = torch.optim.Adam(W_PARAMETERS , lr = 0.001)
        return optimizer

def get_model():
    model = Baseline()
    extended = Extended(model)

    return extended

def test_training():
    from dataloader import get_training_dataset, get_final_test_dataset, get_dataloaders
    import pytorch_lightning
    from pytorch_lightning.loggers import TensorBoardLogger

    train_loader, val_loader = get_dataloaders()
    model = get_model()

    logger = TensorBoardLogger(save_dir="lightning_logs", name="finding_overfitting_point", version="v2_"+str(Universal_Apprioximate_Function))

    trainer = pytorch_lightning.Trainer(enable_progress_bar = True , max_epochs=10, logger=logger)
    trainer.fit(model, train_loader, val_loader)

if __name__=="__main__":
    test_training()