import { createRoot } from 'react-dom/client';
import Iridescence from '@/components/Iridescence';

let mountedRoot;

export function mount(container) {
  if (!container || mountedRoot) return;

  mountedRoot = createRoot(container);
  mountedRoot.render(
    <Iridescence
      color={[0.78, 0.72, 0.9]}
      speed={0.16}
      amplitude={0.08}
      scale={1.45}
      detail={5}
      warp={0.55}
      saturation={0.56}
      brightness={1.08}
      contrast={0.9}
      stir={0.12}
      sheen={0.14}
      clickSwirl={false}
      fade={0.18}
      opacity={0.58}
      resolution={0.38}
      className="libero-iridescence-canvas"
    />,
  );
}

export function unmount() {
  mountedRoot?.unmount();
  mountedRoot = undefined;
}
