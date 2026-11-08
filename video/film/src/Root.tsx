import { Composition } from "remotion";
import { Episode } from "./Episode";
import data from "./episode.generated.json";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="SemanticAfterlife"
        component={Episode}
        durationInFrames={data.duration}
        fps={data.fps}
        width={data.width}
        height={data.height}
      />
    </>
  );
};
