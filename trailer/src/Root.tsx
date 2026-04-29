import "./index.css";
import { Composition } from "remotion";
import { MyComposition } from "./Composition";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="QuietLineTeaser"
        component={MyComposition}
        durationInFrames={1350}
        fps={30}
        width={1280}
        height={720}
      />
    </>
  );
};
