package com.pyritone.bridge.mixin;

import net.minecraft.text.MutableText;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(targets = "baritone.api.utils.Helper", remap = false)
public interface BaritoneHelperPrefixMixin {
    @Inject(method = "getPrefix", at = @At("HEAD"), cancellable = true, remap = false)
    private static void pyritone$overridePrefix(CallbackInfoReturnable<Text> cir) {
        MutableText prefix = Text.literal("");
        prefix.append(Text.literal("[").formatted(Formatting.DARK_PURPLE));
        prefix.append(Text.literal("Py-Ritone").formatted(Formatting.LIGHT_PURPLE));
        prefix.append(Text.literal("]").formatted(Formatting.DARK_PURPLE));
        cir.setReturnValue(prefix);
    }
}

